from locust import HttpUser, task, between

class HotItemShopper(HttpUser):
    wait_time = between(0.5, 1.0)
    token = ""
    
    def on_start(self):
        """
        가상 유저가 생성되자마자 가장 먼저 실행되는 로직 (로그인)
        """

        login_data = {
            "username": "admin",
            "password": "admin1234"
        }

        response = self.client.post("/api/accounts/login/", json=login_data)
        if response.status_code == 200:
            self.token = response.json().get("access")

    @task
    def buy_limited_item(self):
        """
        메인 부하 테스트 타겟: 나이키 조던 1 (item_id: 1) 구매 버튼 연타
        """
        if self.token:
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            payload = {
                "item_id": 1
            }
            with self.client.post("/api/shop/orders/", json=payload, headers=headers, catch_response=True) as response:
                if response.status_code == 201:
                    response.success()
                elif response.status_code == 400:
                    response.success()
                else:
                    response.failure(f"Unexpected status code: {response.status_code}")
    ""
    