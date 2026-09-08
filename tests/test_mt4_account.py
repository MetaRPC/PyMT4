import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'package'))

from MetaRpcMT4.mt4_account import MT4Account, ConnectExceptionMT4, ApiExceptionMT4
from MetaRpcMT4 import mt4_term_api_connection_pb2 as conn_pb
from MetaRpcMT4 import mt4_term_api_account_helper_pb2 as helper_pb


class TestMT4Account(unittest.TestCase):
    def test_account_initialization(self):
        account = MT4Account(user=12345678, password="test_password", grpc_server="custom.mt4:443", api_key="test_key")
        self.assertEqual(account.user, 12345678)
        self.assertEqual(account.password, "test_password")
        self.assertEqual(account.grpc_server, "custom.mt4:443")
        self.assertEqual(account.api_key, "test_key")

    def test_default_grpc_server(self):
        account = MT4Account(user=12345678, password="test_password")
        self.assertEqual(account.grpc_server, "mt4.mrpc.pro:443")

    def test_get_headers_with_auth(self):
        account = MT4Account(user=12345678, password="test_password", id_="test-guid", api_key="my_api_key")
        headers = account.get_headers()
        self.assertIn(("id", "test-guid"), headers)
        self.assertIn(("apikey", "my_api_key"), headers)

    def test_connect_request_proto(self):
        req = conn_pb.ConnectRequest(
            user=12345678,
            password="test_password",
            host="127.0.0.1",
            port=443
        )
        self.assertEqual(req.user, 12345678)
        self.assertEqual(req.password, "test_password")
        self.assertEqual(req.host, "127.0.0.1")
        self.assertEqual(req.port, 443)

    def test_get_id_request_proto(self):
        req = conn_pb.GetIdRequest(
            user="12345678",
            password="test_password"
        )
        self.assertEqual(req.user, "12345678")
        self.assertEqual(req.password, "test_password")

        reply = conn_pb.GetIdReply(
            data=conn_pb.GetIdData(id="68c935ee-a2b1-4f3e-bb36-3982845cfa85")
        )
        self.assertEqual(reply.data.id, "68c935ee-a2b1-4f3e-bb36-3982845cfa85")

    def test_account_summary_data_proto(self):
        data = helper_pb.AccountSummaryData(
            account_login=12345678,
            account_balance=5000.00,
            account_equity=5100.00,
            account_currency="USD",
            account_leverage=500
        )
        self.assertEqual(data.account_login, 12345678)
        self.assertAlmostEqual(data.account_balance, 5000.00)
        self.assertAlmostEqual(data.account_equity, 5100.00)
        self.assertEqual(data.account_currency, "USD")
        self.assertEqual(data.account_leverage, 500)

    def test_exceptions(self):
        exc = ConnectExceptionMT4("connection failed")
        self.assertIn("connection failed", str(exc))

        api_exc = ApiExceptionMT4("order error")
        self.assertIn("order error", str(api_exc))


if __name__ == "__main__":
    unittest.main()
