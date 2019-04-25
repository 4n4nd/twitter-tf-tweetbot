ENV_FILE := .env
include ${ENV_FILE}
export $(shell sed 's/=.*//' ${ENV_FILE})
export PIPENV_DOTENV_LOCATION=${ENV_FILE}

oc_deploy_master:
	oc process --filename=openshift/twitterbot-master-deployment-template.yaml \
		--param TWITTER_CONSUMER_KEY=${MASTER_TWITTER_CONSUMER_KEY} \
		--param TWITTER_CONSUMER_SECRET=${MASTER_TWITTER_CONSUMER_SECRET} \
		--param TWITTER_ACCESS_TOKEN="${MASTER_TWITTER_ACCESS_TOKEN}" \
		--param TWITTER_ACCESS_TOKEN_SECRET="${MASTER_TWITTER_ACCESS_TOKEN_SECRET}" \
		--param FLT_DEBUG_MODE="${FLT_DEBUG_MODE}" \
		--param FLT_LOAD_TESTING_MODE="${FLT_LOAD_TESTING_MODE}" \
		| oc apply -f -

oc_deploy_chatbot_worker:
	oc process --filename=openshift/twitter-chatbot-worker-deployment-template.yaml \
		--param TWITTER_CONSUMER_KEY=${CHATBOT_TWITTER_CONSUMER_KEY} \
		--param TWITTER_CONSUMER_SECRET=${CHATBOT_TWITTER_CONSUMER_SECRET} \
		--param TWITTER_ACCESS_TOKEN="${CHATBOT_TWITTER_ACCESS_TOKEN}" \
		--param TWITTER_ACCESS_TOKEN_SECRET="${CHATBOT_TWITTER_ACCESS_TOKEN_SECRET}" \
		--param FLT_DEBUG_MODE="${FLT_DEBUG_MODE}" \
		--param FLT_LOAD_TESTING_MODE="${FLT_LOAD_TESTING_MODE}" \
		| oc apply -f -

oc_deploy_tweetbot_worker:
	oc process --filename=openshift/twitter-tweetbot-worker-deployment-template.yaml \
		--param TWITTER_CONSUMER_KEY=${TWEETBOT_TWITTER_CONSUMER_KEY} \
		--param TWITTER_CONSUMER_SECRET=${TWEETBOT_TWITTER_CONSUMER_SECRET} \
		--param TWITTER_ACCESS_TOKEN="${TWEETBOT_TWITTER_ACCESS_TOKEN}" \
		--param TWITTER_ACCESS_TOKEN_SECRET="${TWEETBOT_TWITTER_ACCESS_TOKEN_SECRET}" \
		--param FLT_DEBUG_MODE="${FLT_DEBUG_MODE}" \
		--param FLT_LOAD_TESTING_MODE="${FLT_LOAD_TESTING_MODE}" \
		| oc apply -f -

oc_deploy_tf_serving:
	oc new-app -fhttps://raw.githubusercontent.com/4n4nd/oc-tf-model-serving/master/oc-deployment-template.yaml

oc_deploy_acme:
	oc create -fhttps://raw.githubusercontent.com/tnozicka/openshift-acme/master/deploy/letsencrypt-live/single-namespace/{role,serviceaccount,imagestream,deployment}.yaml
	oc policy add-role-to-user openshift-acme --role-namespace="$(oc project --short)" -z openshift-acme

oc_deploy_all: oc_deploy_tf_serving oc_deploy_chatbot_worker oc_deploy_tweetbot_worker oc_deploy_master

oc_delete_master_deployment:
	oc delete all -l app=twitterbot-master

oc_delete_chatbot_deployment:
	oc delete all -l app=twitter-chatbot-worker

oc_delete_tweetbot_deployment:
	oc delete all -l app=twitter-tweetbot-worker

oc_delete_tf_serving_deployment:
	oc delete all -l app=tensorflow-model-serving

oc_delete_all: oc_delete_tf_serving_deployment oc_delete_master_deployment 	oc_delete_chatbot_deployment oc_delete_tweetbot_deployment

register_webhook:
	pipenv run python register_webhook.py
