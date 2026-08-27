from dataclasses import dataclass


@dataclass(slots=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    latency_seconds: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class BudgetCapExceeded(RuntimeError):
    """Raised when a local demo exceeds the configured token or dollar cap."""


@dataclass(slots=True)
class BudgetMeter:
    token_cap: int
    usd_cap: float
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0

    def add(self, *, input_tokens: int, output_tokens: int, estimated_cost_usd: float) -> None:
        next_input = self.input_tokens + input_tokens
        next_output = self.output_tokens + output_tokens
        next_cost = self.estimated_cost_usd + estimated_cost_usd
        if next_input + next_output > self.token_cap or next_cost > self.usd_cap:
            raise BudgetCapExceeded(
                f"Charge denied: would reach {next_input + next_output} tokens and ${next_cost:.4f}."
            )
        self.input_tokens = next_input
        self.output_tokens = next_output
        self.estimated_cost_usd = next_cost

    def snapshot(self, *, latency_seconds: float = 0.0) -> Usage:
        return Usage(
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            estimated_cost_usd=self.estimated_cost_usd,
            latency_seconds=latency_seconds,
        )
