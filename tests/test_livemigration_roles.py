import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class TestScvmmLiveMigrationRole(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = (REPO_ROOT / 'roles/scvmm_livemigration/tasks/main.yml').read_text(encoding='utf-8')

    def test_validation_allows_only_supported_auth_protocols(self):
        self.assertIn("(live_migration.auth_protocol | string) in ['CredSSP', 'Kerberos']", self.content)
        self.assertIn("(item.live_migration.auth_protocol | string) in ['CredSSP', 'Kerberos']", self.content)

    def test_validation_allows_only_supported_performance_modes(self):
        self.assertIn("(live_migration.performance_option | string) in ['TCPIP', 'Compression', 'SMB']", self.content)
        self.assertIn("(item.live_migration.performance_option | string) in ['TCPIP', 'Compression', 'SMB']", self.content)

    def test_cluster_update_supports_check_mode(self):
        self.assertIn('WOULD_CHANGE:', self.content)
        self.assertIn('CHANGED:', self.content)
        self.assertRegex(
            self.content,
            re.compile(r"\(ansible_check_mode or scvmm_live_migration\.check_only\)")
        )


class TestHypervLiveMigrationRole(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = (REPO_ROOT / 'roles/hyperv_livemigration/tasks/main.yml').read_text(encoding='utf-8')

    def test_change_detection_uses_before_after_diff(self):
        expected_markers = [
            '$before = Get-VMHost',
            '$after = Get-VMHost',
            "Write-Output 'CHANGED'",
            "Write-Output 'UNCHANGED'",
        ]
        for marker in expected_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.content)

    def test_changed_when_relies_on_changed_output_marker(self):
        self.assertIn("changed_when: \"'CHANGED' in (hyperv_lm.output | join(' '))\"", self.content)


if __name__ == '__main__':
    unittest.main()
