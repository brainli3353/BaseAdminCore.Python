from __future__ import annotations

from enum import IntEnum


class DataScopeEnum(IntEnum):
    All = 1
    OrgAndChild = 2
    Org = 3
    Self = 4
    Define = 5


class NoticeTypeEnum(IntEnum):
    Notice = 1
    Announcement = 2
    Upgrade = 3


class NoticeStatusEnum(IntEnum):
    Draft = 0
    Public = 1
    Cancel = 2
    Deleted = 3


class NoticeUserStatusEnum(IntEnum):
    Unread = 0
    Read = 1


class MessageTypeEnum(IntEnum):
    Info = 0
    Success = 1
    Warning = 2
    Error = 3


class ResetIntervalEnum(IntEnum):
    Never = 0
    Day = 1
    Month = 2
    Year = 3


class PrintTypeEnum(IntEnum):
    Browser = 1
    Client = 2
