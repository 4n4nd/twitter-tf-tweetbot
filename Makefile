ENV_FILE := .env
include ${ENV_FILE}
export $(shell sed 's/=.*//' ${ENV_FILE})
export PIPENV_DOTENV_LOCATION=${ENV_FILE}

oc_deploy:
	oc process --filename=openshift/twitterbot-master-deployment-template.yaml \
		--param TWITTER_CONSUMER_KEY=${TWITTER_CONSUMER_KEY} \
		--param TWITTER_CONSUMER_SECRET=${TWITTER_CONSUMER_SECRET} \
		--param TWITTER_ACCESS_TOKEN="${TWITTER_ACCESS_TOKEN}" \
		--param TWITTER_ACCESS_TOKEN_SECRET="${TWITTER_ACCESS_TOKEN_SECRET}" \
		--param FLT_DEBUG_MODE="${FLT_DEBUG_MODE}" \
		| oc apply -f -

oc_delete_deployment:
	oc delete all -l app=twitterbot-master-demo

run_app:
	pipenv run python master.py
