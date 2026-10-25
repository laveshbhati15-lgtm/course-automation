"""Supported site adapters for course inspection and automation."""

from course_automation.sites.base import BaseSiteAdapter
from course_automation.sites.codechef.adapter import CodeChefAdapter

__all__ = ["BaseSiteAdapter", "CodeChefAdapter"]
