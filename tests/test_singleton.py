from pytest import raises

from just_start.singleton import Singleton


def test_singleton_is_created_once(mocker):
    class TestSingleton(Singleton):
        pass

    init_instance = _create_test_init(mocker)
    for _ in range(2):
        TestSingleton(init_instance).lower()

    init_instance.assert_called_once()


def test_singleton_is_not_recreated_after_attribute_error(mocker):
    class TestSingleton(Singleton):
        pass

    init_instance = _create_test_init(mocker)
    for _ in range(2):
        with raises(AttributeError):
            TestSingleton(init_instance).invalid_method()

    init_instance.assert_called_once()


def _create_test_init(mocker):
    return mocker.MagicMock(return_value='test')
