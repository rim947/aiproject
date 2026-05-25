import httpx

async def fetch_image_bytes(url: str) -> tuple[bytes, str]:
    print(f"🔍 이미지 다운로드 시도: {url}")
    async with httpx.AsyncClient(follow_redirects=True) as http:
        res = await http.get(url)
        print(f"🔍 응답 상태코드: {res.status_code}")
        res.raise_for_status()
        content_type = res.headers.get("content-type", "image/jpeg").split(";")[0]
        return res.content, content_type
