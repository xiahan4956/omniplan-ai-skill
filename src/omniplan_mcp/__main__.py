from omniplan_mcp.app import mcp
from omniplan_mcp import tasks, documents  # noqa: F401 - registers tools


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
