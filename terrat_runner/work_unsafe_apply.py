import logging
import os
import tempfile

import repo_config as rc
import work_exec
import workflow_step


def _fix_up_apply(steps):
    ret = []
    for s in steps:
        if s['type'] == 'apply':
            s = s.copy()
            s['type'] = 'unsafe_apply'

        ret.append(s)

    return ret


class Exec(work_exec.ExecInterface):
    def pre_hooks(self, state):
        return [{'type': 'checkout'}] + rc.get_apply_hooks(state.repo_config)['pre']

    def post_hooks(self, state):
        return rc.get_apply_hooks(state.repo_config)['post']

    def exec(self, state, d):
        with tempfile.TemporaryDirectory() as tmpdir:
            logging.debug('EXEC : DIR : %s', d['path'])

            # Need to reset output every iteration unfortunately because we do not
            # have immutable dicts
            state = state._replace(outputs=[])

            path = d['path']
            workspace = d['workspace']
            workflow_idx = d.get('workflow')

            env = state.env.copy()
            env['TERRATEAM_DIR'] = path
            env['TERRATEAM_WORKSPACE'] = workspace
            env['TERRATEAM_TMPDIR'] = tmpdir

            create_and_select_workspace = rc.get_create_and_select_workspace(
                state.repo_config,
                path)

            logging.info('UNSAFE_APPLY : CREATE_AND_SELECT_WORKSPACE : %s : %r',
                         path,
                         create_and_select_workspace)

            if create_and_select_workspace:
                env['TF_WORKSPACE'] = workspace

            if workflow_idx is None:
                workflow = rc.get_default_workflow(state.repo_config)
            else:
                workflow = rc.get_workflow(state.repo_config, workflow_idx)

            env['TERRATEAM_TERRAFORM_VERSION'] = workflow['terraform_version']
            state = state._replace(env=env)

            state = workflow_step.run_steps(
                state._replace(working_dir=os.path.join(state.working_dir, path),
                               path=path,
                               workspace=workspace,
                               workflow=workflow),
                _fix_up_apply(workflow['apply']))

            result = {
                'path': path,
                'workspace': workspace,
                'success': not state.failed,
                'outputs': state.outputs.copy(),
            }

            return (state, result)