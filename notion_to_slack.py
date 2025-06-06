import requests, os
from datetime import datetime, timedelta

def extract_text_from_block(block):
        block_type = block["type"]
        rich_texts = block.get(block_type, {}).get("rich_text", [])
        if not rich_texts:
            return None

        text = "".join([rt["plain_text"] for rt in rich_texts])

        if block_type == "heading_3":
            return f"*{text}*"  # Slackの太字
        else:
            return f"• {text}"  # 箇条書き

def main():
    # 日付のフィルタ
    yesterday = (datetime.utcnow() + timedelta(hours=9) - timedelta(days=1)).date().isoformat()

    notion_token = os.environ["NOTION_API_KEY"]
    database_id = os.environ["DATABASE_ID"]
    slack_webhook = os.environ["SLACK_WEBHOOK_URL"]

    """ for local testing, you can use a credential.py file with the following content:
    # credential.py
    import credential as c
    notion_token = c.notion_api_key
    database_id = c.database_id
    slack_webhook = c.slack_webhook_url
    """    

    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    # 日報ページの検索
    query = {
        "filter": {
            "property": "日付",
            "date": {
                "equals": yesterday
            }
        }
    }

    resp = requests.post(f"https://api.notion.com/v1/databases/{database_id}/query", headers=headers, json=query)
    pages = resp.json()["results"]

    if not pages:
        text = f"⚠️ {yesterday} の日報が見つかりませんでした。"
    else:
        page_id = pages[0]["id"]
        print(f"Found page ID: {page_id}")
        children = requests.get(f"https://api.notion.com/v1/blocks/{page_id}/children", headers=headers).json()
        #print(children)
        text_blocks = []
        for block in children["results"]:
            text = extract_text_from_block(block)
            if text:
                text_blocks.append(text)

        text = f"📝 {yesterday} の日報:\n" + "\n".join(text_blocks)
        print(text)

    # Slackに通知
    requests.post(slack_webhook, json={"text": text})


if __name__ == "__main__":
    main()