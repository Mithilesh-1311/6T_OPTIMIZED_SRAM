from services.ml.pipeline import train

def test_fixed_grouped_evaluation_is_repeatable():
    first=train()
    second=train()
    assert first==second
    assert first['targets']['quiet_power_uw']['n_groups']==4
    assert first['targets']['hold_snm_mv']['interpolation_baseline']['supported_cases']==2
