from strategy_validator.cli.rollout_ops import main


def test_rollout_ops_event_log_commands_still_parse_helpfully(capsys):
    for command in [
        'oracle-event-log-append',
        'oracle-derived-view',
        'oracle-horizon-view',
        'oracle-rolling-review',
        'oracle-rolling-review-checkpoint',
        'oracle-event-checkpoint',
        'oracle-horizon-checkpoint',
        'verify-oracle-event-checkpoint',
    ]:
        try:
            main([command, '--help'])
        except SystemExit as exc:
            assert exc.code == 0
    out = capsys.readouterr().out
    assert 'oracle-event-log-append' in out
    assert 'verify-oracle-event-checkpoint' in out
