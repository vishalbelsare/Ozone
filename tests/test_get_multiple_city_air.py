import numpy
import pandas
import pandas.api.types as pd_types
import pytest

from utils import (
    api,
    DEFAULT_OUTPUT_FOLDER,
    DEFAULT_OUTPUT_FILE,
    SUPPORTED_OUTPUT_FORMATS,
)


@pytest.mark.vcr
def test_return_value_and_format():
    result = api.get_multiple_city_air(["london", "new delhi", "paris"])
    assert isinstance(result, pandas.DataFrame)
    assert len(result) == 3  # One row per city


@pytest.mark.vcr
def test_column_expected_contents():
    result = api.get_multiple_city_air(["london", "new delhi", "paris"])
    assert result["city"].tolist() == ["london", "new delhi", "paris"]


@pytest.mark.vcr
def test_column_types():
    result = api.get_multiple_city_air(["london", "new delhi", "paris"])
    STR_COLUMNS = [
        "dominant_pollutant",
        "AQI_meaning",
        "AQI_health_implications",
        "timestamp",
        "timestamp_timezone",
    ]
    FLOAT_COLUMNS = [
        "latitude",
        "longitude",
        "aqi",
        "pm2.5",
        "pm10",
        "o3",
        "co",
        "no2",
        "so2",
        "dew",
        "h",
        "p",
        "t",
        "w",
        "wg",
    ]
    assert all([pd_types.is_string_dtype(result[col]) for col in STR_COLUMNS])
    assert all([pd_types.is_float_dtype(result[col]) for col in FLOAT_COLUMNS])


@pytest.mark.vcr
def test_excluded_params():
    # Param should be really excluded when specified as such
    custom_params = ["aqi", "pm2.5", "o3"]
    result = api.get_multiple_city_air(
        ["london", "new delhi", "paris"], params=custom_params
    )
    assert "pm10" not in result
    assert "pm2.5" in result


@pytest.mark.vcr
def test_nonexistent_requested_params():
    # Return asked params wven when the response does not contain that specific param
    BAD_PARAM_NAME = "param_that_is_not_in_london_aqi"
    result = api.get_multiple_city_air(
        ["london", "new delhi", "paris"], params=[BAD_PARAM_NAME]
    )
    param_value = result.at[0, BAD_PARAM_NAME]
    assert numpy.isnan(param_value)


@pytest.mark.vcr
def test_bad_city():
    # NOTE, QUESTION
    # In get_multiple_city_air, it will be annoying if giving one
    # invalid city also halts the entire data collecting process for
    # other valid cities. For example, imagine mass-collecting data
    # for a lot of cities at once using this method only to get aborted
    # because there's one city that don't have AQI station (and raises
    # Exception).
    result = api.get_multiple_city_air(
        ["london", "paris", "a definitely nonexistent city"]
    )

    # The third row should have the "nonexistent city name" intact ...
    assert result.at[2, "city"] == "a definitely nonexistent city"

    # ... and nothing else.
    assert result.iloc[2, :].drop("city").isna().all()


@pytest.mark.vcr
def test_output_data_format_bad():
    with pytest.raises(Exception, match="Invalid file format"):
        api.get_multiple_city_air(
            ["london", "new delhi", "paris"],
            data_format="a definitely wrong data format",
        )

    # Calling wrong data format shouldn't create an output folder
    assert not DEFAULT_OUTPUT_FOLDER.exists()


@pytest.mark.vcr
@pytest.mark.parametrize("fmt", SUPPORTED_OUTPUT_FORMATS)
def test_output_data_formats(fmt):
    # Not specifying data format shouldn't create an output directory
    api.get_multiple_city_air(["london", "new delhi", "paris"])
    assert not DEFAULT_OUTPUT_FOLDER.exists()

    # Output files should be made
    api.get_multiple_city_air(["london", "new delhi", "paris"], data_format=fmt)
    assert DEFAULT_OUTPUT_FILE.with_suffix(f".{fmt}").is_file()
