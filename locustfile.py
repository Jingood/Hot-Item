from locust import HttpUser, task, between
import random

class HotItemShopper(HttpUser):
    wait_time = between(0.5, 1.0)
    token = ""
    
    def on_start(self):
        """
        가상 유저 생성 시 1~500번 중 랜덤으로 한 명의 유저를 선택하여 로그인
        """
        user_id = random.randint(1, 500)
        login_data = {
            "username": f"dummy{user_id}",
            "password": "testpass123!"
        }

        response = self.client.post("/api/accounts/login/", json=login_data)
        if response.status_code == 200:
            self.token = response.json().get("access")
        else:
            print(f"로그인 실패: dummy{user_id}")

    @task
    def buy_limited_item(self):
        """
        실제 부하 테스트: 각기 다른 유저들이 하나의 상품(ID: 1)을 동시에 구매 시도
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
                    response.failure(f"에러 발생: {response.status_code}")
    ""