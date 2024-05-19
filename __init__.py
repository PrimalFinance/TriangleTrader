import asyncio

from Trader.trader import TriangleArbitrage


async def main():
    # !WARNING Item 1&2 should always be in terms of the same currency. C should be the outlier.
    # Ex: ["ETH/USD", "BTC/USD", "ETH/BTC"]
    pairs = ["ETH/USD", "BTC/USD", "ETH/BTC"]
    wait_time = 3
    t = TriangleArbitrage(pairs, sleeptime=wait_time, min_arb_percent=0.3)
    while True:
        task1 = loop.create_task(t.get_quote(pairs[0]))
        task2 = loop.create_task(t.get_quote(pairs[1]))
        task3 = loop.create_task(t.get_quote(pairs[2]))
        # Wait for the tasks to finish
        await asyncio.wait([task1, task2, task3])
        await t.check_arb()
        # # Wait for the value of waitTime between each quote request
        await asyncio.sleep(wait_time)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
