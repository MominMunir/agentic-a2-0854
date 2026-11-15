"""Write a short-lived local inspection token privately; never print it."""

from gigbid_core.config import ROOT
from gigbid_core.db import User, db
from gigbid_core.security import token

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    with db() as session:
        user = session.query(User).filter_by(email=os.environ["REVIEWER_EMAIL"]).first()
        if not user:
            raise SystemExit("Seed the reviewer account first")
        value = token(user.id, "mcp", ttl=3600, server="portfolio")
    path = ROOT / ".private/portfolio-mcp-token.txt"
    path.parent.mkdir(exist_ok=True)
    path.write_text(value, encoding="utf-8")
    print("One-hour inspection token written to ignored .private/portfolio-mcp-token.txt.")
