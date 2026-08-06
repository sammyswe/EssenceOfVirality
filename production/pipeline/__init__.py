"""Pipeline stage implementations.

Stage order: jobspec -> inspector -> audio_analysis -> creative -> render ->
quality -> posting. Orchestration lives in ``orchestrator``; the learning
subsystems (feedback, preferences, experiments, analytics) sit alongside.
"""
