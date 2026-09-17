"""A fee-aware, fully invested buy-and-hold reference, never an order source."""

from dataclasses import asdict, dataclass

from .config import D, down
from .market import Quote


@dataclass(frozen=True)
class HodlBenchmark:
    initial_cash: str
    fee_rate: str
    entry_tick: int
    entry_quote: dict
    base_size: str
    cash: str
    entry_fee: str

    @classmethod
    def start(cls, initial_cash, quote, fee_rate, entry_tick):
        capital, rate = D(initial_cash), D(fee_rate)
        if capital <= 0 or not 0 <= rate <= D(".05"):
            raise ValueError("Invalid HODL capital or fee")
        if type(entry_tick) is not int or entry_tick < 1:
            raise ValueError("Positive integer HODL entry tick required")
        size = down(capital / (quote.ask * (1 + rate)), quote.base_increment)
        if size < quote.minimum_base or size * quote.ask < quote.minimum_quote:
            size = D(0)
        value = size * quote.ask
        fee = value * rate
        return cls(
            str(capital), str(rate), entry_tick, quote.json(),
            str(size), str(capital - value - fee), str(fee),
        )

    @classmethod
    def restore(cls, record):
        saved = cls(**record)
        quote = Quote(**{
            k: v if k in ("product", "timestamp") else D(v)
            for k, v in saved.entry_quote.items()
        })
        expected = cls.start(saved.initial_cash, quote, saved.fee_rate, saved.entry_tick)
        if saved != expected:
            raise ValueError("HODL benchmark accounting mismatch")
        return saved

    def equity(self, quote):
        if quote.product != self.entry_quote["product"]:
            raise ValueError("HODL product mismatch")
        if quote.timestamp < self.entry_quote["timestamp"]:
            raise ValueError("HODL mark precedes entry quote")
        return D(self.cash) + D(self.base_size) * quote.bid

    def json(self):
        return asdict(self)

    def mark(self, quote, portfolio_equity):
        value = self.equity(quote)
        return {
            "reference": self.json(),
            "equity_usdc": str(value),
            "shortfall_usdc": str(max(D(0), value - D(portfolio_equity))),
        }
