"""
Pipeline Scheduling Tests

Tests that verify pipeline schedules are properly configured and active.
This addresses the critical gap where schedules may exist but not execute.
"""

import sys
from datetime import datetime

import pytest

sys.path.insert(0, "/home/src")


@pytest.mark.integration
class TestPipelineScheduling:
    """驗證管道排程配置和執行狀態"""

    def test_schedules_exist_in_database(self):
        """
        驗證所有必要的排程存在於 Mage 資料庫中

        這個測試確保：
        1. 排程已經被創建
        2. 排程與正確的管道關聯
        3. 排程處於活躍狀態
        """
        try:
            from mage_ai.orchestration.db import db_connection
            from mage_ai.orchestration.db.models.schedules import (
                PipelineSchedule,
                ScheduleStatus,
            )

            # 啟動資料庫連接
            db_connection.start_session()

            # 定義必須存在的排程
            required_schedules = {
                "btc_price_daily": "btc_price_pipeline",
                "news_hourly": "news_ingestion_pipeline",
                "sentiment_2hourly": "news_sentiment_pipeline",
                "features_6hourly": "feature_integration_pipeline",
            }

            missing_schedules = []
            inactive_schedules = []

            for schedule_name, pipeline_uuid in required_schedules.items():
                schedule = (
                    PipelineSchedule.query.filter(
                        PipelineSchedule.name == schedule_name
                    )
                    .filter(PipelineSchedule.pipeline_uuid == pipeline_uuid)
                    .first()
                )

                if schedule is None:
                    missing_schedules.append(
                        f"{schedule_name} (pipeline: {pipeline_uuid})"
                    )
                elif schedule.status != ScheduleStatus.ACTIVE:
                    inactive_schedules.append(
                        f"{schedule_name} (status: {schedule.status})"
                    )

            # 組合錯誤訊息
            error_messages = []
            if missing_schedules:
                error_messages.append(f"❌ 缺少排程: {', '.join(missing_schedules)}")
            if inactive_schedules:
                error_messages.append(f"⚠️ 非活躍排程: {', '.join(inactive_schedules)}")

            assert not error_messages, "\n".join(error_messages)

            print(f"✅ 所有 {len(required_schedules)} 個排程都存在且處於活躍狀態")

        except ImportError as e:
            pytest.skip(f"無法導入 Mage 模組，跳過測試: {e}")

    def test_schedule_intervals_correct(self):
        """
        驗證排程間隔設定正確

        這個測試確保：
        1. 排程的執行頻率符合預期
        2. Cron 表達式格式正確
        3. 排程時間設定合理
        """
        try:
            from mage_ai.orchestration.db import db_connection

            # mage_ai legacy import removed

            db_connection.start_session()

            # 定義預期的排程間隔
            expected_intervals = {
                "btc_price_daily": "@daily",  # 每天執行一次
                "news_hourly": "@hourly",  # 每小時執行一次
                "sentiment_2hourly": "0 */2 * * *",  # 每 2 小時執行
                "features_6hourly": "0 */6 * * *",  # 每 6 小時執行
            }

            mismatched_intervals = []

            for schedule_name, expected_interval in expected_intervals.items():
                schedule = PipelineSchedule.query.filter(
                    PipelineSchedule.name == schedule_name
                ).first()

                if schedule is None:
                    continue  # 由其他測試處理缺失的排程

                actual_interval = schedule.schedule_interval

                if actual_interval != expected_interval:
                    mismatched_intervals.append(
                        f"{schedule_name}: 期望 '{expected_interval}', "
                        f"實際 '{actual_interval}'"
                    )

            assert not mismatched_intervals, f"排程間隔設定錯誤:\n" + "\n".join(
                mismatched_intervals
            )

            print("✅ 所有排程間隔設定正確")

        except ImportError as e:
            pytest.skip(f"無法導入 Mage 模組，跳過測試: {e}")

    def test_schedule_start_times_set(self):
        """
        驗證排程有設定開始時間

        沒有開始時間的排程可能永遠不會執行
        """
        try:
            from mage_ai.orchestration.db import db_connection
            from mage_ai.orchestration.db.models.schedules import (
                PipelineSchedule,
                ScheduleStatus,
            )

            db_connection.start_session()

            schedules = PipelineSchedule.query.filter(
                PipelineSchedule.status == ScheduleStatus.ACTIVE
            ).all()

            schedules_without_start_time = []

            for schedule in schedules:
                if schedule.start_time is None:
                    schedules_without_start_time.append(schedule.name)

            assert not schedules_without_start_time, (
                f"以下排程沒有設定開始時間，可能無法執行: "
                f"{', '.join(schedules_without_start_time)}"
            )

            print(f"✅ 所有 {len(schedules)} 個活躍排程都有開始時間")

        except ImportError as e:
            pytest.skip(f"無法導入 Mage 模組，跳過測試: {e}")

    def test_pipelines_referenced_by_schedules_exist(self):
        """
        驗證排程引用的管道實際存在

        避免「排程存在但管道不存在」的情況
        """
        try:
            from mage_ai.data_preparation.models.pipeline import Pipeline
            from mage_ai.orchestration.db import db_connection
            from mage_ai.orchestration.db.models.schedules import (
                PipelineSchedule,
                ScheduleStatus,
            )

            db_connection.start_session()

            active_schedules = PipelineSchedule.query.filter(
                PipelineSchedule.status == ScheduleStatus.ACTIVE
            ).all()

            missing_pipelines = []

            for schedule in active_schedules:
                try:
                    # 嘗試載入管道
                    Pipeline.get(schedule.pipeline_uuid, repo_path=schedule.repo_path)
                except Exception as e:
                    missing_pipelines.append(
                        f"{schedule.name} -> {schedule.pipeline_uuid} ({str(e)})"
                    )

            assert (
                not missing_pipelines
            ), f"以下排程引用的管道不存在或無法載入:\n" + "\n".join(missing_pipelines)

            print(f"✅ 所有 {len(active_schedules)} 個排程的管道都存在")

        except ImportError as e:
            pytest.skip(f"無法導入 Mage 模組，跳過測試: {e}")


@pytest.mark.integration
class TestPipelineExecutionHistory:
    """驗證管道執行歷史和狀態"""

    def test_pipelines_have_execution_history(self):
        """
        驗證管道有執行歷史記錄

        如果管道從未執行過，可能表示排程有問題
        """
        try:
            from mage_ai.orchestration.db import db_connection
            from mage_ai.orchestration.db.models.pipeline_runs import PipelineRun
            from mage_ai.orchestration.db.models.schedules import (
                PipelineSchedule,
                ScheduleStatus,
            )

            db_connection.start_session()

            active_schedules = PipelineSchedule.query.filter(
                PipelineSchedule.status == ScheduleStatus.ACTIVE
            ).all()

            pipelines_never_run = []

            for schedule in active_schedules:
                # 查詢該管道的執行記錄
                runs = (
                    PipelineRun.query.filter(
                        PipelineRun.pipeline_uuid == schedule.pipeline_uuid
                    )
                    .order_by(PipelineRun.created_at.desc())
                    .limit(1)
                    .all()
                )

                if not runs:
                    pipelines_never_run.append(
                        f"{schedule.name} ({schedule.pipeline_uuid})"
                    )

            # 這是警告而不是錯誤，因為新部署的系統可能沒有執行歷史
            if pipelines_never_run:
                print(
                    f"⚠️ 警告：以下管道從未執行過:\n" + "\n".join(pipelines_never_run)
                )
                print("這可能是正常的（如果是新部署）或表示排程未正常工作")
            else:
                print("✅ 所有活躍管道都有執行歷史")

        except ImportError as e:
            pytest.skip(f"無法導入 Mage 模組，跳過測試: {e}")

    def test_recent_pipeline_runs_not_all_failed(self):
        """
        驗證最近的管道執行不是全部失敗

        如果所有最近的執行都失敗，說明有系統性問題
        """
        try:
            from mage_ai.orchestration.db import db_connection
            from mage_ai.orchestration.db.models.pipeline_runs import (
                PipelineRun,
                PipelineRunStatus,
            )
            from mage_ai.orchestration.db.models.schedules import (
                PipelineSchedule,
                ScheduleStatus,
            )

            db_connection.start_session()

            active_schedules = PipelineSchedule.query.filter(
                PipelineSchedule.status == ScheduleStatus.ACTIVE
            ).all()

            pipelines_all_failed = []

            for schedule in active_schedules:
                # 查詢最近 5 次執行
                recent_runs = (
                    PipelineRun.query.filter(
                        PipelineRun.pipeline_uuid == schedule.pipeline_uuid
                    )
                    .order_by(PipelineRun.created_at.desc())
                    .limit(5)
                    .all()
                )

                if not recent_runs:
                    continue  # 沒有執行歷史，跳過

                # 檢查是否所有執行都失敗
                all_failed = all(
                    run.status == PipelineRunStatus.FAILED for run in recent_runs
                )

                if all_failed:
                    pipelines_all_failed.append(
                        f"{schedule.name} (最近 {len(recent_runs)} 次執行全部失敗)"
                    )

            assert (
                not pipelines_all_failed
            ), f"以下管道最近的執行全部失敗，表示有嚴重問題:\n" + "\n".join(
                pipelines_all_failed
            )

            print("✅ 沒有管道的最近執行全部失敗")

        except ImportError as e:
            pytest.skip(f"無法導入 Mage 模組，跳過測試: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
