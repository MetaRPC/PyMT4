"""
Trade calls must never be re-sent automatically after a transport failure whose outcome
is unknown. Uses a real in-process grpc.aio server on 127.0.0.1 with fake servicers.
"""
import os
import sys
import unittest

import grpc
import grpc.aio

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'package'))
sys.path.insert(0, ROOT)

from MetaRpcMT4 import MT4Account, TradeOutcomeUnknownError, ApiExceptionMT4
from MetaRpcMT4 import mrpc_mt4_error_pb2 as error_pb2
from MetaRpcMT4 import mt4_term_api_connection_pb2 as conn_pb2
from MetaRpcMT4 import mt4_term_api_connection_pb2_grpc as conn_grpc
from MetaRpcMT4 import mt4_term_api_account_helper_pb2 as acc_pb2
from MetaRpcMT4 import mt4_term_api_account_helper_pb2_grpc as acc_grpc
from MetaRpcMT4 import mt4_term_api_trading_helper_pb2 as trade_pb2
from MetaRpcMT4 import mt4_term_api_trading_helper_pb2_grpc as trade_grpc
from app.Helper.errors import map_backend_error, MT4Error, OrderRejected, ModifyRejected, TradeOutcomeUnknown

GUID = "11111111-2222-3333-4444-555555555555"


class Script:
    """Per-method list of planned failures, consumed one per call; afterwards: success."""

    def __init__(self):
        self.calls = {}
        self.plan = {}

    def take(self, method):
        self.calls[method] = self.calls.get(method, 0) + 1
        steps = self.plan.get(method) or []
        return steps.pop(0) if steps else None


async def _answer(script, method, context, reply_cls, data):
    step = script.take(method)
    if step is None:
        return reply_cls(data=data)
    kind, value = step
    if kind == "status":
        code, details = value
        await context.abort(code, details)
    return reply_cls(error=error_pb2.Error(error_code=value, error_message=f"{value} (fake)"))


class FakeConnection(conn_grpc.ConnectionServicer):
    def __init__(self, script):
        self.script = script

    async def ConnectEx(self, request, context):
        return await _answer(self.script, "ConnectEx", context, conn_pb2.ConnectExReply,
                             conn_pb2.ConnectData(terminal_instance_guid=GUID))


class FakeAccount(acc_grpc.AccountHelperServicer):
    def __init__(self, script):
        self.script = script

    async def AccountSummary(self, request, context):
        return await _answer(self.script, "AccountSummary", context, acc_pb2.AccountSummaryReply,
                             acc_pb2.AccountSummaryData(account_login=42))


class FakeTrading(trade_grpc.TradingHelperServicer):
    def __init__(self, script):
        self.script = script

    async def OrderSend(self, request, context):
        return await _answer(self.script, "OrderSend", context, trade_pb2.OrderSendReply,
                             trade_pb2.OrderSendData(ticket=7))

    async def OrderModify(self, request, context):
        return await _answer(self.script, "OrderModify", context, trade_pb2.OrderModifyReply,
                             trade_pb2.OrderModifyData(order_was_modified=True))

    async def OrderCloseDelete(self, request, context):
        return await _answer(self.script, "OrderCloseDelete", context, trade_pb2.OrderCloseDeleteReply,
                             trade_pb2.OrderCloseDeleteData())

    async def OrderCloseBy(self, request, context):
        return await _answer(self.script, "OrderCloseBy", context, trade_pb2.OrderCloseByReply,
                             trade_pb2.OrderCloseByData(profit=1.0))


class NoTradeReplayTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.script = Script()
        self.server = grpc.aio.server()
        conn_grpc.add_ConnectionServicer_to_server(FakeConnection(self.script), self.server)
        acc_grpc.add_AccountHelperServicer_to_server(FakeAccount(self.script), self.server)
        trade_grpc.add_TradingHelperServicer_to_server(FakeTrading(self.script), self.server)
        port = self.server.add_insecure_port("127.0.0.1:0")
        await self.server.start()

        self.account = MT4Account(user=1, password="x", api_key="test-key", id_=GUID)
        await self.account.channel.close()
        channel = grpc.aio.insecure_channel(f"127.0.0.1:{port}")
        self.account.channel = channel
        self.account.connection_client = conn_grpc.ConnectionStub(channel)
        self.account.account_client = acc_grpc.AccountHelperStub(channel)
        self.account.trade_client = trade_grpc.TradingHelperStub(channel)
        self.account.server_name = "Fake-Demo"  # as after connect_by_server_name

    async def asyncTearDown(self):
        await self.account.channel.close()
        await self.server.stop(None)

    def calls(self, method):
        return self.script.calls.get(method, 0)

    def send(self):
        return self.account.order_send("EURUSD", trade_pb2.OrderSendOperationType.Value(
            trade_pb2.OrderSendOperationType.keys()[0]), 0.01)

    async def test_trade_transport_failure_is_not_resent(self):
        cases = [
            ("OrderSend", self.send),
            ("OrderModify", lambda: self.account.order_modify(7, new_stop_loss=1.0)),
            ("OrderCloseDelete", lambda: self.account.order_close_delete(7)),
            ("OrderCloseDelete", lambda: self.account.order_close_delete(7, lots=0.01)),  # partial close
            ("OrderCloseBy", lambda: self.account.order_close_by(7, 8)),
        ]
        codes = [grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED,
                 grpc.StatusCode.UNKNOWN, grpc.StatusCode.INTERNAL]
        for method, call in cases:
            for code in codes:
                with self.subTest(method=method, code=code.name):
                    before = self.calls(method)
                    self.script.plan[method] = [("status", (code, "transport broke"))]
                    with self.assertRaises(TradeOutcomeUnknownError) as cm:
                        await call()
                    ex = cm.exception
                    self.assertEqual(self.calls(method) - before, 1)
                    self.assertEqual(self.calls("ConnectEx"), 0)
                    self.assertEqual(ex.error_code, "TRADE_OUTCOME_UNKNOWN")
                    self.assertEqual(ex.error.error_code, "TRADE_OUTCOME_UNKNOWN")
                    self.assertEqual(ex.operation, method)
                    self.assertEqual(ex.code(), code)
                    self.assertEqual(ex.details(), "transport broke")
                    self.assertIsInstance(ex.transport_error, grpc.aio.AioRpcError)
                    self.assertIs(ex.__cause__, ex.transport_error)
                    self.assertIsInstance(ex, grpc.RpcError)
                    self.assertIsInstance(ex, grpc.aio.AioRpcError)
                    self.assertIsInstance(ex, ApiExceptionMT4)
                    self.assertTrue(str(ex).startswith(f"TRADE_OUTCOME_UNKNOWN: {method} failed with gRPC {code.name}"))
                    self.assertIn("NOT re-sent", str(ex))

    async def test_trade_terminal_instance_not_found_reconnects_and_resends(self):
        self.script.plan["OrderSend"] = [("inband", "TERMINAL_INSTANCE_NOT_FOUND")]
        data = await self.send()
        self.assertEqual(data.ticket, 7)
        self.assertEqual(self.calls("OrderSend"), 2)
        self.assertEqual(self.calls("ConnectEx"), 1)

    async def test_read_unavailable_is_retried(self):
        self.script.plan["AccountSummary"] = [("status", (grpc.StatusCode.UNAVAILABLE, "transport broke"))]
        data = await self.account.account_summary()
        self.assertEqual(data.account_login, 42)
        self.assertEqual(self.calls("AccountSummary"), 2)
        self.assertEqual(self.calls("ConnectEx"), 1)

    async def test_api_key_invalid_in_band_fails_fast(self):
        for method, call in [("AccountSummary", lambda: self.account.account_summary()), ("OrderSend", self.send)]:
            with self.subTest(method=method):
                self.script.plan[method] = [("inband", "API_KEY_INVALID")]
                with self.assertRaises(ApiExceptionMT4) as cm:
                    await call()
                self.assertEqual(cm.exception.error.error_code, "API_KEY_INVALID")
                self.assertEqual(self.calls(method), 1)
                self.assertEqual(self.calls("ConnectEx"), 0)

    async def test_in_band_error_code_without_message_is_raised(self):
        # Before: an error carrying only error_code (no message) was returned as success.
        reply = acc_pb2.AccountSummaryReply(error=error_pb2.Error(error_code="API_KEY_REQUIRED"))

        async def grpc_call(headers):
            self.script.take("CodeOnly")
            return reply

        with self.assertRaises(ApiExceptionMT4) as cm:
            await self.account.execute_with_reconnect(grpc_call, lambda r: r.error)
        self.assertEqual(cm.exception.error.error_code, "API_KEY_REQUIRED")
        self.assertEqual(self.calls("CodeOnly"), 1)
        self.assertEqual(self.calls("ConnectEx"), 0)

    async def test_api_key_refusal_in_status_does_not_reconnect(self):
        for code_text in ("API_KEY_INVALID", "API_KEY_REQUIRED"):
            for method, call in [("AccountSummary", lambda: self.account.account_summary()), ("OrderSend", self.send)]:
                with self.subTest(code=code_text, method=method):
                    before = self.calls(method)
                    self.script.plan[method] = [("status", (grpc.StatusCode.UNAVAILABLE, f"{code_text}: refused"))]
                    with self.assertRaises(grpc.aio.AioRpcError) as cm:
                        await call()
                    self.assertNotIsInstance(cm.exception, TradeOutcomeUnknownError)
                    self.assertIn(code_text, cm.exception.details())
                    self.assertEqual(self.calls(method) - before, 1)
                    self.assertEqual(self.calls("ConnectEx"), 0)

    async def test_sugar_error_mapping_keeps_unknown_outcome(self):
        self.script.plan["OrderSend"] = [("status", (grpc.StatusCode.UNAVAILABLE, "transport broke"))]
        try:
            await self.send()
        except Exception as e:
            mapped = map_backend_error(e, context="order_send", payload={"symbol": "EURUSD"})
        self.assertIsInstance(mapped, TradeOutcomeUnknown)
        self.assertIsInstance(mapped, MT4Error)
        self.assertNotIsInstance(mapped, (OrderRejected, ModifyRejected))
        self.assertEqual(mapped.error_code, "TRADE_OUTCOME_UNKNOWN")
        self.assertEqual(mapped.operation, "OrderSend")
        self.assertEqual(mapped.transport_error.code(), grpc.StatusCode.UNAVAILABLE)
        self.assertIsInstance(mapped.details, TradeOutcomeUnknownError)
        # other errors keep their old mapping
        self.assertIsInstance(map_backend_error(RuntimeError("x"), context="order_send"), OrderRejected)

    async def test_execute_with_reconnect_positional_signature_unchanged(self):
        async def grpc_call(headers):
            return await self.account.account_client.AccountSummary(acc_pb2.AccountSummaryRequest(), metadata=headers)
        res = await self.account.execute_with_reconnect(grpc_call, lambda r: getattr(r, "error", None), None, None)
        self.assertEqual(res.data.account_login, 42)


if __name__ == "__main__":
    unittest.main()
