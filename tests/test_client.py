
import pytest


@pytest.fixture
def app(mocker):
    mocked_session = mocker.patch('requests.Session')
    from notion_params import NotionParams as NP
    client = NP.get_client()
    client.mocked_request = mocked_session.return_value.request
    yield client
    # cleanup here


def test_client_api(app):
    app.retrieve_bot_user()
    # check
    assert len(app.mocked_request.call_args_list) == 1
    _args, kw = app.mocked_request.call_args_list[0]
    print(kw)
    assert kw == {
        'url': 'https://api.notion.com/v1/users/me',
        'method': 'get',
        'json': None,
    }
