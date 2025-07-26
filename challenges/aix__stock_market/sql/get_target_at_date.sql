SELECT *
FROM `{{ project }}.raw_data_layer.t_target`
WHERE OBS_DATE BETWEEN '{{ start_obs_date }}' AND '{{ end_obs_date }}'