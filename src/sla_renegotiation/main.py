import uvicorn

from sla_renegotiation.config import settings


def main() -> None:
    uvicorn.run(
        "sla_renegotiation.api.server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
