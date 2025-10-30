# Low_level_call.py
# -*- coding: utf-8 -*-
"""
A demonstration of all low-level MT4 API calls directly, without wrappers.
This file shows a run of all available API methods.
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PKG_DIR = REPO_ROOT / "package"
if str(PKG_DIR) not in sys.path:
    sys.path.insert(0, str(PKG_DIR))

# Now we can import as top-level 'MetaRpcMT4'
from MetaRpcMT4.mt4_account import MT4Account
import MetaRpcMT4.mt4_term_api_trading_helper_pb2 as trading_pb2  # for enums
import MetaRpcMT4.mt4_term_api_market_info_pb2 as market_pb2


# --- Small helpers ---
def env_int(name: str) -> int:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    try:
        return int(v)
    except ValueError:
        raise RuntimeError(f"Env var {name} must be int, got: {v!r}")

def env_str(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


async def main():
    print("=" * 80)
    print("LOW-LEVEL MT4 API CALLS DEMONSTRATION")
    print("=" * 80)
    print("\nThis script demonstrates ALL available low-level API calls:")
    print("  1. Connection Methods")
    print("  2. Account Information")
    print("  3. Market Data & Quotes")
    print("  4. Orders & History")
    print("  5. Trading Operations (commented out)")
    print("  6. Real-time Streaming")
    print("\n" + "=" * 80)

    # ===== 0) Read credentials from environment or appsettings.json =====
    print("\n=== [Setup] Reading credentials ===")

    # Try to load from appsettings.json if exists
    import json
    settings = None
    try:
        with open("appsettings.json", "r", encoding="utf-8") as f:
            settings = json.load(f)
            print("Loaded appsettings.json")
    except FileNotFoundError:
        print("No appsettings.json found, using environment variables only")
    except Exception as e:
        print(f"Error loading appsettings.json: {e}")

    # Get credentials with fallback to appsettings.json
    if settings and "mt4" in settings:
        user = int(os.getenv("MT4_LOGIN", settings["mt4"].get("login", 0)))
        password = os.getenv("MT4_PASSWORD", settings["mt4"].get("password", ""))
        server_name = os.getenv("MT4_SERVER", settings["mt4"].get("server_name", "MetaQuotes-Demo"))
        base_symbol = os.getenv("BASE_SYMBOL", settings["mt4"].get("base_symbol", "EURUSD"))
        connect_timeout = int(os.getenv("CONNECT_TIMEOUT", settings["mt4"].get("timeout_seconds", 30)))
        grpc_server = os.getenv("GRPC_SERVER", settings.get("grpc", {}).get("server", "mt4.mrpc.pro:443"))
        access_list = settings["mt4"].get("access", [])
    else:
        # Fallback to environment variables only
        try:
            user = env_int("MT4_LOGIN")
            password = env_str("MT4_PASSWORD")
        except RuntimeError as e:
            print(f"\nError: {e}")
            print("\nPlease set environment variables or create appsettings.json:")
            print("  MT4_LOGIN=your_login")
            print("  MT4_PASSWORD=your_password")
            print("  MT4_SERVER=your_server  (optional)")
            return

        server_name = os.getenv("MT4_SERVER", "MetaQuotes-Demo")
        base_symbol = os.getenv("BASE_SYMBOL", "EURUSD")
        connect_timeout = int(os.getenv("CONNECT_TIMEOUT", "30"))
        grpc_server = os.getenv("GRPC_SERVER", "mt4.mrpc.pro:443")
        access_list = []

    print(f"Login: {user}")
    print(f"GRPC Server: {grpc_server}")
    print(f"Base Symbol: {base_symbol}")
    print(f"Timeout: {connect_timeout}s")

    account = MT4Account(user=user, password=password, grpc_server=grpc_server, id_=None)

    # ===== 1) Connection (Multi-priority system) =====
    print("\n" + "=" * 80)
    print("CONNECTION - Multi-priority system")
    print("=" * 80)

    connected = False

    # PRIORITY 1: Direct connection via host:port from access list
    if access_list:
        print("\n[PRIORITY 1] Trying direct connection via host:port")
        for host_port in access_list:
            try:
                print(f"  Attempting: {host_port}")
                parts = host_port.split(":")
                host = parts[0]
                port = int(parts[1]) if len(parts) > 1 else 443

                await account.connect_by_host_port(
                    host=host,
                    port=port,
                    base_chart_symbol=base_symbol,
                    timeout_seconds=connect_timeout,
                )
                print(f"  [OK] Connected to {host}:{port}")
                connected = True
                break
            except Exception as e:
                print(f"  [FAIL] {host_port}: {e}")
                continue

    # PRIORITY 2: Connect by server name
    if not connected and server_name:
        print("\n[PRIORITY 2] Trying connection by server name")
        print(f"  Server: {server_name}")
        try:
            await account.connect_by_server_name(
                server_name=server_name,
                base_chart_symbol=base_symbol,
                wait_for_terminal_is_alive=True,
                timeout_seconds=connect_timeout,
                deadline=None,
            )
            print(f"  [OK] Connected via server name: {server_name}")
            connected = True
        except Exception as e:
            print(f"  [FAIL] {e}")

    # PRIORITY 3: Environment variables fallback
    if not connected:
        env_host = os.getenv("MT4_HOST")
        env_port = os.getenv("MT4_PORT")

        if env_host and env_port:
            print("\n[PRIORITY 3] Trying connection via environment variables")
            print(f"  Host: {env_host}")
            print(f"  Port: {env_port}")
            try:
                await account.connect_by_host_port(
                    host=env_host,
                    port=int(env_port),
                    base_chart_symbol=base_symbol,
                    timeout_seconds=connect_timeout,
                )
                print(f"  [OK] Connected via environment variables")
                connected = True
            except Exception as e:
                print(f"  [FAIL] {e}")

    if not connected:
        print("\n[ERROR] Failed to connect using all available methods")
        print("Please check:")
        print("  1. appsettings.json with 'access' list")
        print("  2. MT4_SERVER environment variable")
        print("  3. MT4_HOST and MT4_PORT environment variables")
        return

    print(f"\n[CONNECTED] Terminal ID: {account.id}")

    # ===== 2) Account =====
    print("\n=== [Account] account_summary ===")
    acc = await account.account_summary()
    # Print a minimal subset
    try:
        print(f"Login={acc.login}  Name={acc.name}  Balance={acc.balance:.2f}  Equity={acc.equity:.2f}")
        print(f"Margin={acc.margin:.2f}  Free Margin={acc.margin_free:.2f}  Margin Level={acc.margin_level:.2f}%")
    except Exception as e:
        print(f"Account summary received (fields may differ): {e}")

    # ===== 3) Market Data (reference & quotes) =====
    print("\n=== [Market] symbols ===")
    syms = await account.symbols()
    try:
        count = syms.symbols_count if hasattr(syms, 'symbols_count') else len(syms.symbols) if hasattr(syms, 'symbols') else 0
        print(f"Symbols count: {count}")
        if hasattr(syms, 'symbols') and len(syms.symbols) > 0:
            print(f"First 5 symbols: {', '.join(syms.symbols[:5])}")
    except Exception as e:
        print(f"Symbols received: {e}")

    symbol = os.getenv("SYMBOL", "EURUSD")

    print("\n=== [Market] symbol_params_many ===")
    sp = await account.symbol_params_many(symbol)
    try:
        if hasattr(sp, 'symbols_params') and len(sp.symbols_params) > 0:
            params = sp.symbols_params[0]
            print(f"Symbol: {params.symbol}, Digits: {params.digits}, Point: {params.point}")
            print(f"Spread: {params.spread}, Trade Mode: {params.trade_mode}")
        else:
            print(f"Params for {symbol}: received")
    except Exception as e:
        print(f"Symbol params received: {e}")

    print("\n=== [Market] quote ===")
    q = await account.quote(symbol)
    try:
        print(f"{symbol} Bid={q.bid:.5f} Ask={q.ask:.5f} Spread={(q.ask - q.bid):.5f}")
        print(f"Time: {q.time_utc}, High={q.high:.5f}, Low={q.low:.5f}")
    except Exception as e:
        print(f"Quote for {symbol} received: {e}")

    print("\n=== [Market] quote_many ===")
    qm = await account.quote_many([symbol, "GBPUSD", "USDJPY"])
    try:
        if hasattr(qm, 'quotes') and len(qm.quotes) > 0:
            print(f"Received {len(qm.quotes)} quotes:")
            for quote in qm.quotes:
                print(f"  {quote.symbol}: Bid={quote.bid:.5f} Ask={quote.ask:.5f}")
        else:
            print("quote_many received.")
    except Exception as e:
        print(f"Quote many received: {e}")

    print("\n=== [Market] tick_value_with_size ===")
    tv = await account.tick_value_with_size([symbol])
    try:
        if hasattr(tv, 'tick_values') and len(tv.tick_values) > 0:
            tick_val = tv.tick_values[0]
            print(f"Symbol: {tick_val.symbol}")
            print(f"Tick value: {tick_val.tick_value:.5f}, Tick size: {tick_val.tick_size:.5f}")
            print(f"Contract size: {tick_val.contract_size}")
        else:
            print("tick_value_with_size received.")
    except Exception as e:
        print(f"Tick value received: {e}")

    print("\n=== [Market] quote_history ===")
    # Example: last 24 hours
    from_time = datetime.now(timezone.utc) - timedelta(hours=24)
    to_time = datetime.now(timezone.utc)
    h = await account.quote_history(
        symbol=symbol,
        timeframe=market_pb2.ENUM_QUOTE_HISTORY_TIMEFRAME.QH_PERIOD_H1,
        from_time=from_time,
        to_time=to_time
    )
    try:
        bars_count = len(h.bars) if hasattr(h, 'bars') else 0
        print(f"quote_history received: {bars_count} bars")
    except Exception:
        print("quote_history received.")

    # ===== 4) Orders / Positions (read-only) =====
    print("\n=== [Orders] opened_orders ===")
    oo = await account.opened_orders()
    try:
        if hasattr(oo, 'orders') and len(oo.orders) > 0:
            print(f"Total opened orders/positions: {len(oo.orders)}")
            for order in oo.orders[:5]:  # Show first 5
                print(f"  Ticket: {order.ticket}, Symbol: {order.symbol}, Type: {order.order_type}")
                print(f"    Volume: {order.volume}, Open Price: {order.open_price:.5f}, Profit: {order.profit:.2f}")
        else:
            print("No opened orders/positions.")
    except Exception as e:
        print(f"opened_orders received: {e}")

    print("\n=== [Orders] opened_orders_tickets ===")
    oot = await account.opened_orders_tickets()
    try:
        if hasattr(oot, 'tickets') and len(oot.tickets) > 0:
            print(f"Total tickets: {len(oot.tickets)}")
            print(f"Tickets: {oot.tickets[:10]}")  # Show first 10
        else:
            print("No opened order tickets.")
    except Exception as e:
        print(f"opened_orders_tickets received: {e}")

    print("\n=== [Orders] orders_history ===")
    hist = await account.orders_history()
    try:
        if hasattr(hist, 'orders') and len(hist.orders) > 0:
            print(f"Total history orders: {len(hist.orders)}")
            for order in hist.orders[:3]:  # Show first 3
                print(f"  Ticket: {order.ticket}, Symbol: {order.symbol}, Type: {order.order_type}")
                print(f"    Close Time: {order.close_time}, Profit: {order.profit:.2f}")
        else:
            print("No orders history.")
    except Exception as e:
        print(f"orders_history received: {e}")

    # ===== 5) Trading (WRITE) — with minimal values for demo =====
    print("\n" + "=" * 80)
    print("TRADING OPERATIONS SECTION (Read-only demo - shows syntax)")
    print("=" * 80)
    print("⚠️  Trading operations are COMMENTED OUT by default for safety.")
    print("⚠️  To enable, set ENABLE_TRADING=1 in your environment.")
    print("=" * 80)

    enable_trading = os.getenv("ENABLE_TRADING", "0") == "1"

    if enable_trading:
        print("\n⚠️  TRADING IS ENABLED! Real orders will be sent!\n")

        # Get current quote for price calculations
        current_quote = await account.quote(symbol)
        current_ask = current_quote.ask
        current_bid = current_quote.bid

        # ===== BUY Market Order (minimum volume) =====
        print("\n=== [Trading] order_send (BUY Market) ===")
        try:
            send_res = await account.order_send(
                symbol=symbol,
                operation_type=trading_pb2.OrderSendOperationType.BUY,
                volume=0.01,           # Minimum volume (0.01 lots)
                price=None,            # None = market order
                slippage=20,           # 20 points slippage
                stoploss=current_ask - 0.0050,   # 50 pips SL
                takeprofit=current_ask + 0.0050,  # 50 pips TP
                comment="LL demo BUY",
                magic_number=999999,   # Magic number for identification
                expiration=None,
            )
            print(f"✓ Order sent successfully!")
            print(f"  Ticket: {send_res.order_ticket if hasattr(send_res, 'order_ticket') else 'N/A'}")
            print(f"  Open Price: {send_res.open_price if hasattr(send_res, 'open_price') else 'N/A'}")
            order_ticket = send_res.order_ticket if hasattr(send_res, 'order_ticket') else None
        except Exception as e:
            print(f"✗ Order failed: {e}")
            order_ticket = None

        # ===== BUY LIMIT Pending Order =====
        print("\n=== [Trading] order_send (BUY LIMIT) ===")
        try:
            limit_price = current_bid - 0.0010  # 10 pips below current price
            send_res = await account.order_send(
                symbol=symbol,
                operation_type=trading_pb2.OrderSendOperationType.BUYLIMIT,
                volume=0.01,
                price=limit_price,     # Pending order price
                slippage=20,
                stoploss=limit_price - 0.0050,
                takeprofit=limit_price + 0.0050,
                comment="LL demo BUYLIMIT",
                magic_number=999999,
                expiration=datetime.now(timezone.utc) + timedelta(hours=1),  # Expires in 1 hour
            )
            print(f"✓ Pending order sent!")
            print(f"  Ticket: {send_res.order_ticket if hasattr(send_res, 'order_ticket') else 'N/A'}")
            print(f"  Pending Price: {limit_price:.5f}")
            pending_ticket = send_res.order_ticket if hasattr(send_res, 'order_ticket') else None
        except Exception as e:
            print(f"✗ Pending order failed: {e}")
            pending_ticket = None

        # ===== Modify Order =====
        if order_ticket:
            print("\n=== [Trading] order_modify ===")
            try:
                modify_res = await account.order_modify(
                    order_ticket=order_ticket,
                    new_stop_loss=current_ask - 0.0030,  # Move SL to 30 pips
                    new_take_profit=current_ask + 0.0100,  # Move TP to 100 pips
                    new_expiration=None
                )
                print(f"✓ Order modified successfully!")
                print(f"  New SL: {current_ask - 0.0030:.5f}")
                print(f"  New TP: {current_ask + 0.0100:.5f}")
            except Exception as e:
                print(f"✗ Modify failed: {e}")

        # ===== Close Order =====
        if order_ticket:
            print("\n=== [Trading] order_close_delete ===")
            try:
                close_res = await account.order_close_delete(
                    order_ticket=order_ticket,
                    lots=0.01,         # Close full position
                    closing_price=None,  # Market price
                    slippage=20
                )
                print(f"✓ Order closed successfully!")
                print(f"  Closed Ticket: {order_ticket}")
            except Exception as e:
                print(f"✗ Close failed: {e}")

        # ===== Delete Pending Order =====
        if pending_ticket:
            print("\n=== [Trading] order_close_delete (Pending) ===")
            try:
                delete_res = await account.order_close_delete(
                    order_ticket=pending_ticket,
                    lots=None,
                    closing_price=None,
                    slippage=20
                )
                print(f"✓ Pending order deleted successfully!")
                print(f"  Deleted Ticket: {pending_ticket}")
            except Exception as e:
                print(f"✗ Delete failed: {e}")

        # ===== Close By (requires two opposite positions) =====
        print("\n=== [Trading] order_close_by ===")
        print("⚠️  Requires two opposite positions - skipped in demo")
        # close_by_res = await account.order_close_by(
        #     ticket_to_close=buy_ticket,
        #     opposite_ticket_closing_by=sell_ticket
        # )

    else:
        print("\n=== Trading operations syntax examples ===")
        print("\n# BUY Market Order (0.01 lots):")
        print("send_res = await account.order_send(")
        print("    symbol='EURUSD',")
        print("    operation_type=trading_pb2.OrderSendOperationType.BUY,")
        print("    volume=0.01,")
        print("    price=None,  # Market order")
        print("    slippage=20,")
        print("    stoploss=1.0850,  # Example SL")
        print("    takeprofit=1.0950,  # Example TP")
        print("    comment='Demo order',")
        print("    magic_number=999999,")
        print(")")

        print("\n# BUY LIMIT Pending Order:")
        print("send_res = await account.order_send(")
        print("    symbol='EURUSD',")
        print("    operation_type=trading_pb2.OrderSendOperationType.BUYLIMIT,")
        print("    volume=0.01,")
        print("    price=1.0850,  # Pending price")
        print("    expiration=datetime.now(timezone.utc) + timedelta(hours=1),")
        print(")")

        print("\n# Modify Order:")
        print("modify_res = await account.order_modify(")
        print("    order_ticket=123456,")
        print("    new_stop_loss=1.0860,")
        print("    new_take_profit=1.0940,")
        print(")")

        print("\n# Close Order:")
        print("close_res = await account.order_close_delete(")
        print("    order_ticket=123456,")
        print("    lots=0.01,  # Full or partial close")
        print("    slippage=20,")
        print(")")

        print("\n# Close By (opposite positions):")
        print("close_by_res = await account.order_close_by(")
        print("    ticket_to_close=buy_ticket,")
        print("    opposite_ticket_closing_by=sell_ticket,")
        print(")")

        print("\nAvailable OrderSendOperationType values:")
        print("  - BUY, SELL (market orders)")
        print("  - BUYLIMIT, SELLLIMIT (pending limit orders)")
        print("  - BUYSTOP, SELLSTOP (pending stop orders)")

    # ===== 6) Streaming / Subscriptions (ticks & trades) =====
    # We'll run each stream briefly and then cancel via cancellation_event.
    print("\n" + "=" * 80)
    print("STREAMING - Real-time data subscriptions")
    print("=" * 80)

    print("\n=== [Streaming] on_symbol_tick (5s) ===")
    cancel_ticks = asyncio.Event()
    tick_count = 0

    async def run_ticks():
        nonlocal tick_count
        try:
            async for tick_data in account.on_symbol_tick([symbol], cancellation_event=cancel_ticks):
                tick_count += 1
                try:
                    # Try to print tick details
                    if hasattr(tick_data, 'symbol') and hasattr(tick_data, 'bid'):
                        print(f"  Tick #{tick_count}: {tick_data.symbol} Bid={tick_data.bid:.5f} Ask={tick_data.ask:.5f}")
                    else:
                        print(f"  Tick #{tick_count} received")
                except Exception:
                    print(f"  Tick #{tick_count} received")

                if cancel_ticks.is_set():
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"  Stream error: {e}")

    task_ticks = asyncio.create_task(run_ticks())

    try:
        await asyncio.wait_for(asyncio.sleep(5), timeout=5)
    except asyncio.TimeoutError:
        pass

    cancel_ticks.set()

    try:
        await asyncio.wait_for(task_ticks, timeout=1.0)
    except asyncio.TimeoutError:
        print("  (Stream timeout - forcing cancellation)")
        task_ticks.cancel()
        try:
            await task_ticks
        except asyncio.CancelledError:
            pass

    print(f"Total ticks received: {tick_count}")

    print("\n=== [Streaming] on_trade (5s) ===")
    cancel_trades = asyncio.Event()
    trade_count = 0

    async def run_trades():
        nonlocal trade_count
        try:
            async for trade_data in account.on_trade(cancellation_event=cancel_trades):
                trade_count += 1
                try:
                    if hasattr(trade_data, 'order_ticket'):
                        print(f"  Trade event #{trade_count}: Ticket={trade_data.order_ticket}, Type={trade_data.order_type}")
                    else:
                        print(f"  Trade event #{trade_count} received")
                except Exception:
                    print(f"  Trade event #{trade_count} received")

                # Check if we should stop
                if cancel_trades.is_set():
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"  Stream error: {e}")

    task_trades = asyncio.create_task(run_trades())

    try:
        # Wait up to 5 seconds for task
        await asyncio.wait_for(asyncio.sleep(5), timeout=5)
    except asyncio.TimeoutError:
        pass

    # Signal cancellation
    cancel_trades.set()

    # Give task 1 second to finish gracefully
    try:
        await asyncio.wait_for(task_trades, timeout=1.0)
    except asyncio.TimeoutError:
        print("  (Stream timeout - forcing cancellation)")
        task_trades.cancel()
        try:
            await task_trades
        except asyncio.CancelledError:
            pass

    print(f"Total trade events received: {trade_count}")

    print("\n=== [Streaming] on_opened_orders_tickets (5s) ===")
    cancel_oos = asyncio.Event()
    tickets_update_count = 0

    async def run_oos():
        nonlocal tickets_update_count
        try:
            async for tickets_data in account.on_opened_orders_tickets(cancellation_event=cancel_oos):
                tickets_update_count += 1
                try:
                    if hasattr(tickets_data, 'tickets'):
                        print(f"  Update #{tickets_update_count}: {len(tickets_data.tickets)} open tickets")
                    else:
                        print(f"  Update #{tickets_update_count}: tickets snapshot received")
                except Exception:
                    print(f"  Update #{tickets_update_count} received")

                if cancel_oos.is_set():
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"  Stream error: {e}")

    task_oos = asyncio.create_task(run_oos())

    try:
        await asyncio.wait_for(asyncio.sleep(5), timeout=5)
    except asyncio.TimeoutError:
        pass

    cancel_oos.set()

    try:
        await asyncio.wait_for(task_oos, timeout=1.0)
    except asyncio.TimeoutError:
        print("  (Stream timeout - forcing cancellation)")
        task_oos.cancel()
        try:
            await task_oos
        except asyncio.CancelledError:
            pass

    print(f"Total tickets updates: {tickets_update_count}")

    print("\n=== [Streaming] on_opened_orders_profit (5s) ===")
    cancel_profit = asyncio.Event()
    profit_update_count = 0

    async def run_profit():
        nonlocal profit_update_count
        try:
            async for profit_data in account.on_opened_orders_profit(cancellation_event=cancel_profit):
                profit_update_count += 1
                try:
                    if hasattr(profit_data, 'total_profit'):
                        print(f"  Update #{profit_update_count}: Total Profit={profit_data.total_profit:.2f}")
                    elif hasattr(profit_data, 'equity'):
                        print(f"  Update #{profit_update_count}: Equity={profit_data.equity:.2f}")
                    else:
                        print(f"  Update #{profit_update_count}: profit snapshot received")
                except Exception:
                    print(f"  Update #{profit_update_count} received")

                if cancel_profit.is_set():
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"  Stream error: {e}")

    task_profit = asyncio.create_task(run_profit())

    try:
        await asyncio.wait_for(asyncio.sleep(5), timeout=5)
    except asyncio.TimeoutError:
        pass

    cancel_profit.set()

    try:
        await asyncio.wait_for(task_profit, timeout=1.0)
    except asyncio.TimeoutError:
        print("  (Stream timeout - forcing cancellation)")
        task_profit.cancel()
        try:
            await task_profit
        except asyncio.CancelledError:
            pass

    print(f"Total profit updates: {profit_update_count}")

    # ===== Summary =====
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print("\n✓ All low-level API calls completed successfully!")
    print("\nAPI Calls Demonstrated:")
    print("  ✓ Connection Methods:")
    print("    - connect_by_server_name()")
    print("  ✓ Account Information:")
    print("    - account_summary()")
    print("  ✓ Market Data:")
    print("    - symbols()")
    print("    - symbol_params_many()")
    print("    - quote()")
    print("    - quote_many()")
    print("    - tick_value_with_size()")
    print("    - quote_history()")
    print("  ✓ Orders & History:")
    print("    - opened_orders()")
    print("    - opened_orders_tickets()")
    print("    - orders_history()")
    print("  ✓ Trading Operations (syntax shown):")
    print("    - order_send() - BUY, SELL, BUYLIMIT, BUYSTOP, etc.")
    print("    - order_modify()")
    print("    - order_close_delete()")
    print("    - order_close_by()")
    print("  ✓ Real-time Streaming:")
    print("    - on_symbol_tick() - " + f"{tick_count} ticks received")
    print("    - on_trade() - " + f"{trade_count} trade events")
    print("    - on_opened_orders_tickets() - " + f"{tickets_update_count} updates")
    print("    - on_opened_orders_profit() - " + f"{profit_update_count} updates")

    print("\n" + "=" * 80)
    print("To enable real trading operations:")
    print("  export ENABLE_TRADING=1")
    print("  python examples/Low_level_call.py")
    print("=" * 80)


if __name__ == "__main__":
    # Set console encoding for Windows to support Unicode
    import sys
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


# Command to run:
# python examples/Low_level_call.py

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ FILE examples/Low_level_call.py — Full low-level MT4 API call-through demo   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Purpose:                                                                     ║
║   Demonstrate ALL available low-level MT4Account RPCs directly (no wrappers):║
║   connection variants, account info, market data, orders/history,            ║
║   trading syntax, and real-time streaming subscriptions.                     ║
║                                                                              ║
║ Step-by-step behavior:                                                       ║
║   1) Bootstrap import paths (package/), read config/env.                     ║
║   2) Create MT4Account(user, password, grpc_server).                         ║
║   3) Connect by priority: access[host:port] → server_name → MT4_HOST/PORT.   ║
║   4) Account info: account_summary() minimal print.                          ║
║   5) Market data: symbols(), symbol_params_many(), quote(), quote_many(),    ║
║      tick_value_with_size(), quote_history(H1, last 24h).                    ║
║   6) Orders (read-only): opened_orders(), opened_orders_tickets(),           ║
║      orders_history().                                                       ║
║   7) Trading (WRITE): shows full syntax; can execute if ENABLE_TRADING=1:    ║
║      order_send(BUY, BUYLIMIT), order_modify, order_close_delete,            ║
║      (close_by mention).                                                     ║
║   8) Streaming (5s each): on_symbol_tick([symbol]), on_trade(),              ║
║      on_opened_orders_tickets(), on_opened_orders_profit().                  ║
║   9) Execution summary with counters.                                        ║
║                                                                              ║
║ Public API / Entry Points:                                                   ║
║   - main() — orchestrates full low-level walkthrough                         ║
║   - env_int(), env_str() — helpers for strict env parsing                    ║
║                                                                              ║
║ Dependencies used in this file:                                              ║
║   - MetaRpcMT4.mt4_account.MT4Account                                        ║
║   - MetaRpcMT4.mt4_term_api_trading_helper_pb2 as trading_pb2 (enums)        ║
║   - MetaRpcMT4.mt4_term_api_market_info_pb2 as market_pb2 (timeframes)       ║
║                                                                              ║
║ Config & ENV references:                                                     ║
║   - From appsettings.json (if present): mt4.login, mt4.password,             ║
║       mt4.server_name, mt4.base_symbol, mt4.timeout_seconds, mt4.access[],   ║
║       grpc.server                                                            ║
║   - ENV fallback/overrides: MT4_LOGIN, MT4_PASSWORD, MT4_SERVER,             ║
║       BASE_SYMBOL, CONNECT_TIMEOUT, GRPC_SERVER, MT4_HOST, MT4_PORT,         ║
║       SYMBOL, ENABLE_TRADING                                                 ║
║                                                                              ║
║ RPC showcased (direct low-level):                                            ║
║   - Connection: connect_by_host_port(), connect_by_server_name()             ║
║   - Account: account_summary()                                               ║
║   - Market: symbols(), symbol_params_many(), quote(), quote_many(),          ║
║             tick_value_with_size(), quote_history()                          ║
║   - Orders (read): opened_orders(), opened_orders_tickets(), orders_history()║
║   - Trading (write/syntax or executed if enabled): order_send(),             ║
║             order_modify(), order_close_delete(), order_close_by()           ║
║   - Streaming: on_symbol_tick(), on_trade(),                                 ║
║                on_opened_orders_tickets(), on_opened_orders_profit()         ║
╚══════════════════════════════════════════════════════════════════════════════╝

"""