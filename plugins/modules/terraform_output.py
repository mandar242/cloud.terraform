#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017, Ryan Scott Brown <ryansb@redhat.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: terraform_output
short_description: Returns Terraform module outputs.
description:
  - Returns Terraform module outputs.
options:
  project_path:
    description:
      - The path to the root of the Terraform directory with the .tfstate file.
    type: path
  binary_path:
    description:
      - The path of a terraform binary to use, relative to the 'service_path' unless you supply an absolute path.
    type: path
  state_file:
    description:
      - Absolute path to an existing Terraform state file whose outputs will be listed.
      - If this is not specified, the default C(terraform.tfstate) in the directory I(project_path) will be used.
    type: path
requirements: [ "terraform" ]
author: "Polona Mihalič (@PolonaM)"
"""

EXAMPLES = """
- name: List outputs from terraform.tfstate in project_dir
  cloud.terraform.terraform_output:
    project_path: '{{ project_dir }}'

- name: List outputs from selected state file in project_dir
  cloud.terraform.terraform_output:
    state_file: '{{ state_file }}'

- name: List outputs from terraform.tfstate in project_dir, use different Terraform version
  cloud.terraform.terraform_output:
    project_path: '{{ project_dir }}'
    binary_path: '{{ terraform_binary }}'
"""

RETURN = """
outputs:
  type: complex # DICT?
  description: A dictionary of all the TF outputs by their assigned name. Use C(.outputs.MyOutputName.value) to access the value.
  returned: on success
  sample: '{"bukkit_arn": {"sensitive": false, "type": "string", "value": "arn:aws:s3:::tf-test-bukkit"}'
  contains:
    sensitive:
      type: bool
      returned: always
      description: Whether Terraform has marked this value as sensitive
    type:
      type: str
      returned: always
      description: The type of the value (string, int, etc)
    value:
      type: str
      returned: always
      description: The value of the output as interpolated by Terraform
"""

import os
import json
from ansible.module_utils.six import integer_types

from ansible.module_utils.basic import AnsibleModule


module = None


def _state_args(state_file):
    if state_file and os.path.exists(state_file):
        return ["-state", state_file]
    if state_file and not os.path.exists(state_file):
        module.fail_json(
            msg='Could not find state_file "{0}", check the path and try again.'.format(
                state_file
            )
        )
    return []


def get_outputs(terraform_binary, project_path, state_file):
    outputs_command = [terraform_binary, "output", "-no-color", "-json"] + _state_args(
        state_file
    )
    rc, outputs_text, outputs_err = module.run_command(
        outputs_command, cwd=project_path
    )
    if rc == 1:
        module.warn(
            "Could not get Terraform outputs. "
            "This usually means none have been defined.\nstdout: {0}\nstderr: {1}".format(
                outputs_text, outputs_err
            )
        )
        outputs = {}
    elif rc != 0:
        module.fail_json(
            msg="Failure when getting Terraform outputs. "
            "Exited {0}.\nstdout: {1}\nstderr: {2}".format(
                rc, outputs_text, outputs_err
            ),
            command=" ".join(outputs_command),
        )
    else:
        outputs = json.loads(outputs_text)

    return outputs


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            project_path=dict(type="path"),
            binary_path=dict(type="path"),
            state_file=dict(type="path"),
        ),
    )

    project_path = module.params.get("project_path")
    bin_path = module.params.get("binary_path")
    state_file = module.params.get("state_file")

    if bin_path is not None:
        terraform_binary = bin_path
    else:
        terraform_binary = module.get_bin_path("terraform", required=True)

    outputs = get_outputs(
        terraform_binary=terraform_binary,
        project_path=project_path,
        state_file=state_file,
    )

    module.exit_json(outputs=outputs)


if __name__ == "__main__":
    main()
