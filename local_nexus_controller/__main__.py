import uvicorn

from local_nexus_controller.settings import settings


def main() -> None:
    uvicorn.run(
        "local_nexus_controller.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )


if __name__ == "__main__":
    main()
