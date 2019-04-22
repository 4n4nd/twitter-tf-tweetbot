# twitter-tf-tweetbot
This application is a twitter bot that replies to direct messages and tweets in which the bot is mentioned.
This bot is divided into 4 different openshift deployments.
* Tensorflow model serving
* Twitter Chatbot Workers
* Twitter Tweetbot Workers
* Twitter Master Workers

Each of them is a separate deployment because that makes them individually scalable, so if more users are interacting with the chatbot (using direct messages), the the number of chatbot workers can be increased easily.


## Deploy Openshift-acme
This will help with automatically getting CA certificates for your public routes.

`make oc_deploy_acme`

## Deploy the tensorflow-model-serving
This will download your stored model from github and deploy it on openshift
(Make sure this is done before the chatbot and tweetbot deployment)

`make oc_deploy_tf_serving`


## Deploy the chatbot-worker
This is the deployment of worker pods, that reply to direct messages

`make oc_deploy_chatbot_worker`

## Deploy the tweetbot-worker
This is the deployment of worker pods, that reply to tweet mentions (@MYTWITTERNAME)

`make oc_deploy_tweetbot_worker`

## Deploy the bot master
This is the deployment of master pods, master pods create a webhook, which receives events like direct messages and tweet mentions using the twitter Account Activity API.

`make oc_deploy_master`

## Deploy all
To deploy all of them, run:

`make oc_deploy_all`

 This will deploy the tensorflow-serving first, then the chatbot/tweetbot workers, then finally the master deployment.

## Delete all deployments

 `make oc_delete_all`
