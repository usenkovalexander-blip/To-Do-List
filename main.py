#!/usr/bin/env python3
"""Точка входа для To-Do List приложения."""

from dotenv import load_dotenv

from todo_app.cli import run

if __name__ == "__main__":
    load_dotenv()
    run()
