import unittest

from routers.payment import _verify_notify_sign, _yungouos_sign


class PaymentSignatureTests(unittest.TestCase):
    def test_sign_is_order_independent(self):
        params_a = {"mch_id": "m1", "out_trade_no": "A100", "total_fee": "49.00"}
        params_b = {"total_fee": "49.00", "out_trade_no": "A100", "mch_id": "m1"}
        self.assertEqual(_yungouos_sign(params_a), _yungouos_sign(params_b))

    def test_verify_notify_sign(self):
        params = {
            "code": "1",
            "outTradeNo": "CS202604150001",
            "payNo": "PAY123456",
            "money": "49.00",
            "mchId": "m1",
        }
        sign = _yungouos_sign(params)
        payload = {**params, "sign": sign}
        self.assertTrue(_verify_notify_sign(payload))


if __name__ == "__main__":
    unittest.main()
