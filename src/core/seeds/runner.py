from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


class Seed:
    order: int = 100

    async def run(self, session: AsyncSession) -> None:
        raise NotImplementedError


SEEDS: list[Seed] = []


def register(seed: type[Seed]) -> type[Seed]:
    SEEDS.append(seed())
    return seed


async def run_seeds(session: AsyncSession) -> None:
    for seed in sorted(SEEDS, key=lambda s: (s.order, type(s).__name__)):
        await seed.run(session)
    await session.commit()
