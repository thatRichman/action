import requests_retry
import workflow


def run(state, config):
    url = state.api_base_url + '/v1/work-manifests/' + state.work_token + '/access-token'
    res = requests_retry.post(url, headers={'authorization': 'bearer ' + state.api_token})

    if res.status_code == 200:
        access_token = res.json()['access_token']
        state.run_time.set_secret(access_token)
        env = state.env.copy()
        env['TERRATEAM_GITHUB_TOKEN'] = access_token
        state = state._replace(env=env)
        return workflow.Result2(success=True,
                                state=state,
                                step='auth/update-terrateam-github-token',
                                payload={})
    else:
        text = """
        Status {}

        {}
        """.format(res.status_code, res.text)
        return workflow.Result2(success=False,
                                state=state,
                                step='auth/update-terrateam-github-token',
                                payload={'text': text})