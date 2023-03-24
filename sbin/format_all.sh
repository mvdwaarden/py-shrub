for project in SHRUB_batch SHRUB_mgmt SHRUB_util SHRUB_openid SHRUB_sec
do
  cd $project
  isort src --profile=black
  black src
  isort tests --profile=black
  black tests
  cd ..
done