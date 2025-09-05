from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from apps.core.templatetags.datetime_utils import format_datetime, relative_time, smart_datetime


class DatetimeUtilsTestCase(TestCase):
    """日時ユーティリティテンプレートフィルターのテスト"""
    
    def setUp(self):
        self.now = timezone.now()
        
    def test_format_datetime_default(self):
        """デフォルトフォーマットのテスト"""
        test_date = datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.get_current_timezone())
        result = format_datetime(test_date)
        self.assertEqual(result, '2024年01月15日 14:30')
        
    def test_format_datetime_date_only(self):
        """日付のみフォーマットのテスト"""
        test_date = datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.get_current_timezone())
        result = format_datetime(test_date, 'date')
        self.assertEqual(result, '2024年01月15日')
        
    def test_format_datetime_time_only(self):
        """時刻のみフォーマットのテスト"""
        test_date = datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.get_current_timezone())
        result = format_datetime(test_date, 'time')
        self.assertEqual(result, '14:30')
        
    def test_format_datetime_short(self):
        """短縮フォーマットのテスト"""
        test_date = datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.get_current_timezone())
        result = format_datetime(test_date, 'short')
        self.assertEqual(result, '01/15 14:30')
        
    def test_format_datetime_slash_date(self):
        """スラッシュ形式日付のテスト"""
        test_date = datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.get_current_timezone())
        result = format_datetime(test_date, 'slash_date')
        self.assertEqual(result, '2024/01/15')
        
    def test_format_datetime_none(self):
        """None値のテスト"""
        result = format_datetime(None)
        self.assertEqual(result, '')
        
    def test_relative_time_minutes(self):
        """分単位の相対時間テスト"""
        test_date = self.now - timedelta(minutes=30)
        result = relative_time(test_date)
        self.assertEqual(result, '30分前')
        
    def test_relative_time_hours(self):
        """時間単位の相対時間テスト"""
        test_date = self.now - timedelta(hours=5)
        result = relative_time(test_date)
        self.assertEqual(result, '5時間前')
        
    def test_relative_time_days(self):
        """日単位の相対時間テスト"""
        test_date = self.now - timedelta(days=3)
        result = relative_time(test_date)
        self.assertEqual(result, '3日前')
        
    def test_relative_time_just_now(self):
        """たった今のテスト"""
        test_date = self.now - timedelta(seconds=30)
        result = relative_time(test_date)
        self.assertEqual(result, 'たった今')
        
    def test_relative_time_future(self):
        """未来日時のテスト"""
        test_date = self.now + timedelta(hours=1)
        result = relative_time(test_date)
        self.assertEqual(result, 'たった今')
        
    def test_relative_time_none(self):
        """None値のテスト"""
        result = relative_time(None)
        self.assertEqual(result, '')
        
    def test_smart_datetime_recent(self):
        """最近の日時のスマート表示テスト"""
        test_date = self.now - timedelta(days=2)
        result = smart_datetime(test_date)
        self.assertEqual(result, '2日前')
        
    def test_smart_datetime_old(self):
        """古い日時のスマート表示テスト"""
        test_date = self.now - timedelta(days=10)
        result = smart_datetime(test_date)
        expected = format_datetime(test_date, 'default')
        self.assertEqual(result, expected)
        
    def test_smart_datetime_old_no_time(self):
        """古い日時の時刻なしスマート表示テスト"""
        test_date = self.now - timedelta(days=10)
        result = smart_datetime(test_date, show_time=False)
        expected = format_datetime(test_date, 'date')
        self.assertEqual(result, expected)