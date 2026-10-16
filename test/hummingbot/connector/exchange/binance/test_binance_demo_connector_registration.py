from unittest import TestCase

from hummingbot.client.settings import AllConnectorSettings


class TestBinanceDemoConnectorRegistration(TestCase):
    def test_binance_demo_is_registered_as_a_binance_subdomain(self):
        settings = AllConnectorSettings.create_connector_settings()
        demo = settings["binance_demo"]

        self.assertEqual("binance", demo.parent_name)
        self.assertEqual("demo", demo.domain_parameter)
        self.assertTrue(demo.is_sub_domain)
        self.assertEqual(
            {"binance_demo_api_key", "binance_demo_api_secret", "connector"},
            set(demo.config_keys.model_fields),
        )
