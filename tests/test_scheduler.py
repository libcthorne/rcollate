import unittest
from unittest.mock import patch

from rcollate import scheduler

def mock_get_job_by_job_key(job_key):
    return {'job_key': job_key}

def mock_get_job_url_by_job_key(job_key):
    return job_key

class StartSchedulerTest(unittest.TestCase):
    @patch('rcollate.scheduler.schedule_job')
    @patch('rcollate.scheduler.BackgroundScheduler.start')
    def test_start_scheduler(self, mock_scheduler_start, mock_schedule_job):
        scheduler.start(
            ['job1', 'job2'],
            mock_get_job_by_job_key,
            mock_get_job_url_by_job_key,
        )

        mock_schedule_job.assert_any_call('job1')
        mock_schedule_job.assert_any_call('job2')
        self.assertEqual(mock_schedule_job.call_count, 2)

        self.assertEqual(mock_scheduler_start.call_count, 1)

class HelpersTest(unittest.TestCase):
    @patch('rcollate.scheduler.run_job')
    @patch('rcollate.scheduler.get_job_by_job_key', mock_get_job_by_job_key)
    def test_run_job_by_job_key(self, mock_run_job):
        scheduler._run_job_by_job_key('test')
        mock_run_job.assert_called_once_with({'job_key': 'test'})
