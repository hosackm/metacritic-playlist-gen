# Metafy
Metafy is an application written in Python that will create a [Spotify playlist](https://open.spotify.com/playlist/65RYrUbKJgX0eJHBIZ14Fe?si=-TBJlxIFQtGiU0dT45Mxqw) of albums that were highly rated on Metacritic.  It does this by using AWS's Serverless Application Model (SAM) to deploy a Lambda Function in the cloud that scrapes Metacritic's [*New Releases*](https://www.metacritic.com/browse/albums/release-date/new-releases/date) page and reads their scores.  In order to deploy it yourself, you'll need an AWS account and a Spotify premium account for manipulating playlists using Spotify's API.

## Prerequisites
Before you can deploy Metafy you'll need to install the AWS/SAM CLI tools and create a Spotify application so you can call the Spotify API.

### Install and configure AWS SAM
You'll need a working installation of the AWS and SAM CLI tools.  Follow the instructions in the [AWS Docs](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)

You can verify that everything is working by running:

    sam --version

### Create a Spotify App
You'll need to create a Spotify App in order to obtain keys to interact with Spotify's API.  Visit [Spotify's Developers Page](https://developer.spotify.com/dashboard/applications) and log in using your username and password.

Click the "Create an App" button and follow the prompts.  Once your application is created you need to add a Redirect URI in the "Edit Settings" section of the dashboard for acquiring a Spotify token later.  Use https://example.com as your URI.

Take note of the following things:

  * Your app's Client ID
  * Your app's Client Secret
  * Your app's Redirect URI

### Create a Spotify Playlist
Create a playlist in your Spotify player of choice.  Right-click (or share on your mobile device) and select the "Copy Spotify URI" option.  This will give you the unique code that references this playlist.

## Installing and Building
Installing and building Metafy is very simple.  Using the SAM command line tools you can build the application.  One of the dependencies requries being built directly in the Lambda container base image.  In order for the builld to succeed you must add the `use-container` option when building:

    sam build --use-container

## Modifying important parameters
The Metafy template uses some placeholders for important parameters.  In order for the application to access Spotify you must correctly replace these. There are two ways to pass the required Spotify credentials to the SAM application.  One is easier and the other is safer.

#### Unsafe parameter overwrites
After cloning this repository, open template.yaml and edit some of the parameters.  You can replace OVERRIDE_ME in the template with your own values that you took note of before.  The following parameters should be updated:

    * SpotifyClientID
    * SpotifyClientSecret
    * SpotifyRefToken
    * SpotifyPlaylistID

#### Pass parameter overrides through CLI
The previous method is considered less safe because it's very easy for someone to upload the credentials to a version control system like git.  A safer option is to pass these credentials through the CLI using the `--parameter-overrides` switch.

To replace the Spotify credentials you can enter them as comma delimited list of `key=value` pairs:

    sam deploy --parameter-overrides SpotifyClientID=<your-client-id>,SpotifyClientSecret=<your-secret>,...(etc.)

The application can be built locally.  The default environment type is set to 'test' using the EnvType parameter.  In this mode the application won't make modifications to your Spotify playlist.  You'll need to change this to 'prod' if you want the application to make calls to the Spotify API.

## Testing Locally
SAM applications allow the user to test Lambda function locally.  In order to this we must invoke the Lambda function directly using the following command:

    sam local invoke MetafyFunction

This will start the container and execute your function in order to simulate an invocation of the Lambda function on AWS.

### Deploying
In order to deploy the application you must run the `sam deploy` command.  In order to override parameters before deploying run the command with the guided option:

    sam deploy --guided

You will have an opportunity to give your deployment a name, select an AWS region, and override some parameters.  Make sure to set `EnvType` to `prod` so that Spotify API requests go live.  If you haven't already placed your Spotify client secret and other parameters in the template.yaml you can do it in the CLI when prompted.
