# Copyright (c) 2015, Daniele Venzano
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from zoe_api.application_validation import ApplicationDescription
from zoe_master.state.execution import Execution
from zoe_master.stats import SchedulerStats


class BaseSchedulerPolicy:
    def __init__(self, platform):
        self.platform = platform

    def admission_control(self, app: ApplicationDescription) -> bool:
        """
        Checks whether an execution requiring the specified resources can be run, now or at a later time. This method can be called
        from outside the scheduler thread, should not have any side effects nor change any state.
        :param app: an application description object describing the resources required by the execution
        :return: True if the execution is possible, False otherwise
        """
        raise NotImplementedError

    def execution_submission(self, execution: Execution) -> None:
        """
        A new execution request has been submitted and needs to scheduled. The request has passed admission control.
        :param execution: the execution to start
        :return:
        """
        raise NotImplementedError

    def execution_kill(self, execution: Execution) -> None:
        """
        An execution has been killed, most probably by the user. Cleanup any status associated with that execution.
        :param execution: the terminated execution
        :return:
        """
        raise NotImplementedError

    def runnable_get(self) -> Execution:
        """
        Fetches an execution that can be run right now. It can modify the application description that is returned,
        respecting the minimums required by the application.
        :return: a tuple (execution, application), or (None, None) if no execution can be started
        """
        raise NotImplementedError

    def start_successful(self, execution: Execution) -> None:
        """
        Update the internal data structures to acknowledge the fact that an execution has been succesfully started.
        :param execution: the execution that was successfully started
        :return: None
        """

    def start_failed(self, execution: Execution) -> None:
        """
        The execution could not be started for a transient error and its startup should be retried again later.
        :param execution: The execution that failed to start
        :return: None
        """

    def stats(self) -> SchedulerStats:
        """
        Gather statistics about the scheduler policy
        :return: a SchedulerStats object
        """
        raise NotImplementedError
