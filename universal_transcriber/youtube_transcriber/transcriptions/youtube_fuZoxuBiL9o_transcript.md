# Transcription: docker stack is my new favorite way to deploy to a VPS

**Video:** [https://youtu.be/fuZoxuBiL9o](https://youtu.be/fuZoxuBiL9o)

[00:00](https://youtu.be/fuZoxuBiL9o?t=0)

For the past few months now, I've been using a VPS when it comes to deploying my applications.

[00:06](https://youtu.be/fuZoxuBiL9o?t=6)

Initially, I achieved this by using Docker Compose, defining my entire application stack inside

[00:11](https://youtu.be/fuZoxuBiL9o?t=11)

of a Docker Compose Yamal file, similar to what I showed in my previous video on setting up

[00:16](https://youtu.be/fuZoxuBiL9o?t=16)

a production ready VPS. For the most part, this has been working well. However, there have been

[00:22](https://youtu.be/fuZoxuBiL9o?t=22)

a couple of things that I've found to be a little unintuitive. One of these things is when it comes

[00:27](https://youtu.be/fuZoxuBiL9o?t=27)

to redeploying my service stack, which I've been doing by manually ssaching into my VPS and

[00:33](https://youtu.be/fuZoxuBiL9o?t=33)

running the Docker Compose up command. Whilst I've managed to make this work, it's not exactly the

[00:38](https://youtu.be/fuZoxuBiL9o?t=38)

best developer experience, especially when compared to the experience of using other platforms,

[00:43](https://youtu.be/fuZoxuBiL9o?t=43)

such as Versel, Netlify or Railway.app. Not only is this a bad developer experience, but because

[00:50](https://youtu.be/fuZoxuBiL9o?t=50)

of the way that Docker Compose works, it also comes with some undesired side effects. The most

[00:56](https://youtu.be/fuZoxuBiL9o?t=56)

major of these is that when you go to redeploy your application stack using the Docker Compose

[01:00](https://youtu.be/fuZoxuBiL9o?t=60)

up command, it does so in a way that can cause downtime. This is because when Docker Compose redeploys,

[01:07](https://youtu.be/fuZoxuBiL9o?t=67)

it begins by shutting down your already running services before attempting to deploy the upgraded ones.

[01:13](https://youtu.be/fuZoxuBiL9o?t=73)

But if there's a problem with your new application code or configuration, then these services

[01:18](https://youtu.be/fuZoxuBiL9o?t=78)

won't be able to start back up, which will cause you to have an outage. Additionally, by needing to

[01:23](https://youtu.be/fuZoxuBiL9o?t=83)

ssh in and copy over the Compose.yaml in order to redeploy, I find this prevents me from being able

[01:29](https://youtu.be/fuZoxuBiL9o?t=89)

to ship fast due to the fact that it's a manual process in order to perform upgrades. Instead,

[01:35](https://youtu.be/fuZoxuBiL9o?t=95)

I'd much rather have a solution that allowed me to easily ship remotely through either my local

[01:39](https://youtu.be/fuZoxuBiL9o?t=99)

machine or via CICD. Similar to what those other platforms I mentioned earlier provide. However,

[01:45](https://youtu.be/fuZoxuBiL9o?t=105)

rather than throwing in the towel and using one of these or pivoting to an entirely different

[01:50](https://youtu.be/fuZoxuBiL9o?t=110)

solution such as Coolify, I instead decided to do some research and look for some other solutions.

[01:56](https://youtu.be/fuZoxuBiL9o?t=116)

And I ended up finding one. One, that not only solves my issues with Docker Compose,

[02:02](https://youtu.be/fuZoxuBiL9o?t=122)

but also allows me to use the same Docker Compose file I already have set up. That solution is

[02:08](https://youtu.be/fuZoxuBiL9o?t=128)

Docker Stack, which has quickly become my favorite way to deploy to a VPS. The way Docker Stack

[02:14](https://youtu.be/fuZoxuBiL9o?t=134)

works is that it allows you to deploy your Docker Compose files on a node that has Docker Swarm Mode

[02:19](https://youtu.be/fuZoxuBiL9o?t=139)

enabled, which is much better suited for production services compared to Docker Compose.

[02:24](https://youtu.be/fuZoxuBiL9o?t=144)

This is because it has support for a number of different features that I think are important when

[02:28](https://youtu.be/fuZoxuBiL9o?t=148)

it comes to running a production service, such as blue green deployments, rolling releases,

[02:34](https://youtu.be/fuZoxuBiL9o?t=154)

secure secrets, service rollbacks, and even clustering. Not only this, but when combined with Docker

[02:40](https://youtu.be/fuZoxuBiL9o?t=160)

context, I'm able to remotely manage and deploy multiple VPS instances from my own workstation,

[02:46](https://youtu.be/fuZoxuBiL9o?t=166)

all in a secure and fast way. For example, let's say I want to make a change to my

[02:51](https://youtu.be/fuZoxuBiL9o?t=171)

guest book web application service stack by adding in a Valky instance. This service is running

[02:57](https://youtu.be/fuZoxuBiL9o?t=177)

on a VPS and is deployed via Docker Stack. In order to do so, all I need to do is open up my

[03:03](https://youtu.be/fuZoxuBiL9o?t=183)

Docker Compose YAML file and add in the following lines to add the Valky service. Then in order to

[03:08](https://youtu.be/fuZoxuBiL9o?t=188)

deploy this, I can run the Docker Stack Deploy command, passing in the Docker Compose file that I

[03:13](https://youtu.be/fuZoxuBiL9o?t=193)

want to use and the name of my stack, which in this case is called "guess book". Then once it's

[03:19](https://youtu.be/fuZoxuBiL9o?t=199)

finished, I can use the following command to check the running services of this guest book stack,

[03:24](https://youtu.be/fuZoxuBiL9o?t=204)

which I can see now has Valky up and running. Order this deployed remotely on my VPS from my

[03:29](https://youtu.be/fuZoxuBiL9o?t=209)

local machine. In addition to this, I'm also able to manage and monitor my application from my

[03:34](https://youtu.be/fuZoxuBiL9o?t=214)

local machine as well, such as being able to view the services logs or add secrets securely.

[03:40](https://youtu.be/fuZoxuBiL9o?t=220)

As well as this, I've also managed to set up Docker Stack to work with my CI/CD pipeline

[03:45](https://youtu.be/fuZoxuBiL9o?t=225)

using GitHub actions, meaning whenever I push a code change to the main branch of my repo,

[03:50](https://youtu.be/fuZoxuBiL9o?t=230)

it'll automatically deploy my entire stack. So yeah, it's a much bigger improvement compared to

[03:56](https://youtu.be/fuZoxuBiL9o?t=236)

using Docker Compose when it comes to working on a VPS. But you may be wondering how difficult

[04:01](https://youtu.be/fuZoxuBiL9o?t=241)

is it to get set up? Well, fortunately, it's actually pretty simple. In fact, I'm going to walk you

[04:07](https://youtu.be/fuZoxuBiL9o?t=247)

through the steps of getting it set up on a VPS from scratch. Before showing you some of the ways

[04:11](https://youtu.be/fuZoxuBiL9o?t=251)

you can use it. To go along with this video, I've created a simple web application using Go.

[04:17](https://youtu.be/fuZoxuBiL9o?t=257)

That we're going to deploy. This app is a simple visitor guest book that tracks the number of visits

[04:22](https://youtu.be/fuZoxuBiL9o?t=262)

to the web page and presents that information to the user, as well as a motivational quote.

[04:27](https://youtu.be/fuZoxuBiL9o?t=267)

The code for this app is available on GitHub, which you can easily pull down yourself.

[04:32](https://youtu.be/fuZoxuBiL9o?t=272)

There's a link in the description down below. If we go ahead and open up this code, you can see that

[04:37](https://youtu.be/fuZoxuBiL9o?t=277)

there's already a Docker file inside, as well as a Docker Compose.yaml. If we open up this file,

[04:43](https://youtu.be/fuZoxuBiL9o?t=283)

we can see that we've defined two distinct services inside the web application and a postgres

[04:49](https://youtu.be/fuZoxuBiL9o?t=289)

database. In addition to having the Docker file and Docker Compose already defined, the application

[04:54](https://youtu.be/fuZoxuBiL9o?t=294)

also has a GitHub action setup as well. Currently, this performs two different automations,

[04:59](https://youtu.be/fuZoxuBiL9o?t=299)

the first of which is running the automated tests, which, if they pass, moves on to the second step,

[05:05](https://youtu.be/fuZoxuBiL9o?t=305)

which is building and pushing a new Docker image of the application to the GitHub container registry.

[05:10](https://youtu.be/fuZoxuBiL9o?t=310)

The interesting thing to note here is that the Docker image itself is tagged with both latest

[05:14](https://youtu.be/fuZoxuBiL9o?t=314)

and the same commit hash that is found at the repo at the time the image is built. This makes it

[05:19](https://youtu.be/fuZoxuBiL9o?t=319)

incredibly easy to correlate the Docker image with the code that it was built from. This is going to

[05:24](https://youtu.be/fuZoxuBiL9o?t=324)

be important later on when it comes to automated deployments. Now that we know what the

[05:28](https://youtu.be/fuZoxuBiL9o?t=328)

application looks like, let's go about getting it deployed. In order to do that, we're going to

[05:33](https://youtu.be/fuZoxuBiL9o?t=333)

need a VPS instance to deploy the application on. Fortunately, that's where the sponsor of today's

[05:38](https://youtu.be/fuZoxuBiL9o?t=338)

video comes in. Hostinger, who have not only provided me with a VPS instance to use throughout

[05:44](https://youtu.be/fuZoxuBiL9o?t=344)

this video, but they also have a Black Friday sale going on until the 15th of December,

[05:49](https://youtu.be/fuZoxuBiL9o?t=349)

meaning you can pick up a long term VPS for an incredibly low price. Up to 67% off. In my case,

[05:56](https://youtu.be/fuZoxuBiL9o?t=356)

I have the KVM2 instance, which not only boasts to VCPUs and a comfy 8GB of RAM,

[06:03](https://youtu.be/fuZoxuBiL9o?t=363)

but it also includes a hundred gigabytes of SSD storage and a huge 8TB a month of bandwidth,

[06:10](https://youtu.be/fuZoxuBiL9o?t=370)

which would set you back over $1,000 if you are using something like Versel. You can pick up a KVM2

[06:16](https://youtu.be/fuZoxuBiL9o?t=376)

instance yourself for only $599 a month when you purchase a 24 month term. Or if you like to go

[06:21](https://youtu.be/fuZoxuBiL9o?t=381)

a little larger, you can put my instance to shame and get yourself a big daddy KVM8, which boasts

[06:27](https://youtu.be/fuZoxuBiL9o?t=387)

a massive 8VCPUs and 32GB of RAM, all for just $1999 a month on a 24 month term. Additionally,

[06:35](https://youtu.be/fuZoxuBiL9o?t=395)

if you use my coupon code "Dreams of Code", you'll also receive an additional discount on any of

[06:40](https://youtu.be/fuZoxuBiL9o?t=400)

these instances, which is incredibly good value. If that wasn't enough, however, hosting

[06:45](https://youtu.be/fuZoxuBiL9o?t=405)

out or also throwing in some premium features as well for Black Friday, including free real-time

[06:50](https://youtu.be/fuZoxuBiL9o?t=410)

snapshots of your VPS and free automatic weekly backups, making it incredibly easy for you to recover

[06:57](https://youtu.be/fuZoxuBiL9o?t=417)

your instance in case something goes wrong. So to get your own VPS instance, visit hostinga.com

[07:03](https://youtu.be/fuZoxuBiL9o?t=423)

forward slash dreams of code and use my coupon code "Dreams of Code" to get that additional

[07:08](https://youtu.be/fuZoxuBiL9o?t=428)

discount. A big thank you to Hostinger for sponsoring this video. With our VPS in hand,

[07:13](https://youtu.be/fuZoxuBiL9o?t=433)

let's go about setting it up in order for us to be able to deploy our Docker stack remotely.

[07:17](https://youtu.be/fuZoxuBiL9o?t=437)

To begin, you'll want to make sure that you're using the same operating system that I am.

[07:21](https://youtu.be/fuZoxuBiL9o?t=441)

You've been to 24.04. Then you'll want to go through the additional steps of securing your

[07:26](https://youtu.be/fuZoxuBiL9o?t=446)

root user by adding in a strong password and setting up your SSH public key. Next, if you have a

[07:32](https://youtu.be/fuZoxuBiL9o?t=452)

spare domain name lying around, then you may want to add a DNS A record to your VPS. If not,

[07:38](https://youtu.be/fuZoxuBiL9o?t=458)

then you can buy a pretty cheap one from Hostinger if you like. Myself, I actually bought the

[07:43](https://youtu.be/fuZoxuBiL9o?t=463)

Zemful site domain to use for this video for only a single dollar. Either way, once your VPS is

[07:49](https://youtu.be/fuZoxuBiL9o?t=469)

set up with your optional A record pointing to it, go ahead and SSH in as your root user. One

[07:55](https://youtu.be/fuZoxuBiL9o?t=475)

thing to note is if you're going to use this VPS as a production machine, then I would recommend

[08:00](https://youtu.be/fuZoxuBiL9o?t=480)

going through the same steps I mentioned in my previous video on setting up a production ready VPS,

[08:05](https://youtu.be/fuZoxuBiL9o?t=485)

such as adding in a user account, hardening SSH and enabling a firewall. For this video,

[08:11](https://youtu.be/fuZoxuBiL9o?t=491)

I'm going to skip all that just so we can get into the good stuff. However, if you don't feel like

[08:16](https://youtu.be/fuZoxuBiL9o?t=496)

watching another video in addition to this one, then I've created a step-by-step guide on the steps

[08:21](https://youtu.be/fuZoxuBiL9o?t=501)

I would normally take, which you can find a link to in the description down below. For this video,

[08:26](https://youtu.be/fuZoxuBiL9o?t=506)

however, now that we're logged in, the next thing we want to do is install the Docker Engine. This

[08:31](https://youtu.be/fuZoxuBiL9o?t=511)

is pretty easy to do so. All we need to do is head on over to the Docker website and copy and

[08:36](https://youtu.be/fuZoxuBiL9o?t=516)

paste the following two commands into our terminal. The first of these is used to add Docker into

[08:41](https://youtu.be/fuZoxuBiL9o?t=521)

the app sources. And the second one is used to install the Docker Engine. You'll notice that in

[08:46](https://youtu.be/fuZoxuBiL9o?t=526)

the second command, I'm ignoring both the build X and compose plugins. This is because we're not

[08:52](https://youtu.be/fuZoxuBiL9o?t=532)

going to need them. So I'm reducing the amount of bloat installed on my system. Once Docker is installed,

[08:57](https://youtu.be/fuZoxuBiL9o?t=537)

we can check that it's working by running the following Docker PS command, which shows us that we're

[09:02](https://youtu.be/fuZoxuBiL9o?t=542)

good to go. With our VPS setup, let's go ahead and now exit out of SSH. As we're going to deploy our

[09:08](https://youtu.be/fuZoxuBiL9o?t=548)

application remotely, then in order to do so, we first need to change our Docker host to be that

[09:13](https://youtu.be/fuZoxuBiL9o?t=553)

of the VPS, which we can do a couple of different ways. The first and easiest way is to just set the

[09:19](https://youtu.be/fuZoxuBiL9o?t=559)

Docker host environment variable, pointing it to the endpoint of our VPS. Whilst this approach works,

[09:25](https://youtu.be/fuZoxuBiL9o?t=565)

instead I prefer to use the Docker context command, which works in a similar way, but allows you to

[09:31](https://youtu.be/fuZoxuBiL9o?t=571)

store and manage multiple different Docker hosts, making it easy to switch between them when you

[09:36](https://youtu.be/fuZoxuBiL9o?t=576)

have multiple machines. To create a new Docker context, we can use the following Docker context

[09:41](https://youtu.be/fuZoxuBiL9o?t=581)

create command, passing in the name we want to give it. Then we can define the Docker endpoint by

[09:46](https://youtu.be/fuZoxuBiL9o?t=586)

using the dash dash Docker flag. As for the value we want to use here, I'm going to define this as

[09:52](https://youtu.be/fuZoxuBiL9o?t=592)

follows, which sets my host to that of an SSH endpoint. Here is how I have my SSH endpoints set up for

[09:58](https://youtu.be/fuZoxuBiL9o?t=598)

my own context. You can see we're specifying the SSH protocol with the SSH colon slash slash,

[10:05](https://youtu.be/fuZoxuBiL9o?t=605)

as well as the username of my user, which is root and the hostname of my VPS. If you don't have a

[10:11](https://youtu.be/fuZoxuBiL9o?t=611)

domain name setup, then you can just use the VPS's IP here instead. Now if I execute this command, my

[10:16](https://youtu.be/fuZoxuBiL9o?t=616)

Docker context should be created. The last thing to do is to make use of it by using the Docker context

[10:22](https://youtu.be/fuZoxuBiL9o?t=622)

use command, passing in the name of the context we just created. Now whenever we perform a Docker

[10:27](https://youtu.be/fuZoxuBiL9o?t=627)

command, instead of this taking place on our local machine, it will instead take place on the

[10:32](https://youtu.be/fuZoxuBiL9o?t=632)

Docker instance of our VPS, allowing us to configure it remotely. With our context defined, we're now

[10:37](https://youtu.be/fuZoxuBiL9o?t=637)

ready to set up our node to use Docker stack. In order to do so, we first need to enable Docker

[10:43](https://youtu.be/fuZoxuBiL9o?t=643)

Swarm mode on our VPS, which we can do using the following Docker Swarm in its command. Upon running

[10:49](https://youtu.be/fuZoxuBiL9o?t=649)

this command, you should then receive a token that will allow you to connect other VPS instances

[10:54](https://youtu.be/fuZoxuBiL9o?t=654)

to this machine in order to form a Docker Swarm cluster. Whilst this is really cool and something

[11:00](https://youtu.be/fuZoxuBiL9o?t=660)

will take a look at another time, we're not going to do that in this video. So you can safely ignore

[11:05](https://youtu.be/fuZoxuBiL9o?t=665)

this token or just save it somewhere else if you want to. But don't worry too much about losing it,

[11:10](https://youtu.be/fuZoxuBiL9o?t=670)

as you can easily obtain this token again if you need. With Swarm mode enabled, we can now deploy

[11:15](https://youtu.be/fuZoxuBiL9o?t=675)

our application using the Docker stack deploy command, passing in the path to our Docker compose.yaml

[11:21](https://youtu.be/fuZoxuBiL9o?t=681)

using the dash c flag. The last argument to this command is to name the stack, which in my case,

[11:27](https://youtu.be/fuZoxuBiL9o?t=687)

I'm going to call Zemful stats. Now when I go and execute this command, we should see some output

[11:32](https://youtu.be/fuZoxuBiL9o?t=692)

letting us know that the stack is being deployed. And once it's completed, if I open up a browser window

[11:37](https://youtu.be/fuZoxuBiL9o?t=697)

and head on over to my domain name of Zemful.site, I can see that my app is now deployed.

[11:43](https://youtu.be/fuZoxuBiL9o?t=703)

Additionally, this remote deployment also works when it comes to private images, like the one that I

[11:48](https://youtu.be/fuZoxuBiL9o?t=708)

have here. If I go ahead and change my compose.yaml file to make use of this private image,

[11:53](https://youtu.be/fuZoxuBiL9o?t=713)

followed by running the Docker stack deploy command, we can see that it's deployed successfully.

[11:58](https://youtu.be/fuZoxuBiL9o?t=718)

However, there is the following warning message that we receive, which is only really an issue

[12:03](https://youtu.be/fuZoxuBiL9o?t=723)

if you're running a Docker Swarm cluster, which in this case we're not. However, to resolve this,

[12:08](https://youtu.be/fuZoxuBiL9o?t=728)

you just need to use the dash dash with registry auth flag with the Docker stack deploy command.

[12:13](https://youtu.be/fuZoxuBiL9o?t=733)

With that, the application is now up and running and we didn't even need to copy anything over

[12:18](https://youtu.be/fuZoxuBiL9o?t=738)

onto our VPS. Now, to be fair, you can actually use both Docker context and Docker host to deploy

[12:24](https://youtu.be/fuZoxuBiL9o?t=744)

Docker compose remotely as well. In fact, this is what I did initially once I discovered it.

[12:30](https://youtu.be/fuZoxuBiL9o?t=750)

However, when doing so, I kept running into an issue that would cause my deployments to fail

[12:35](https://youtu.be/fuZoxuBiL9o?t=755)

whenever I ran Docker compose up. This was because of how Docker compose manages secrets,

[12:41](https://youtu.be/fuZoxuBiL9o?t=761)

which is that they need to be available on the host system in a file. Whilst this in itself

[12:46](https://youtu.be/fuZoxuBiL9o?t=766)

wasn't too difficult to set up, the issue that I had was related to defining the file inside

[12:51](https://youtu.be/fuZoxuBiL9o?t=771)

of the compose.yaml. Initially, I used a relative path, which caused problems when running the

[12:57](https://youtu.be/fuZoxuBiL9o?t=777)

commands remotely, as it would instead resolve to my local machines path instead of the local path

[13:02](https://youtu.be/fuZoxuBiL9o?t=782)

on the remote. Therefore, I needed to instead use the absolute path to the secret file as it related

[13:08](https://youtu.be/fuZoxuBiL9o?t=788)

to my host. But this meant I couldn't use Docker compose locally. Additionally, there was no

[13:14](https://youtu.be/fuZoxuBiL9o?t=794)

easy way to manage the file on the machine without resorting to SSH. And having this secret stored

[13:19](https://youtu.be/fuZoxuBiL9o?t=799)

in plaintext on the machine felt bad from a security perspective, and not very production ready.

[13:25](https://youtu.be/fuZoxuBiL9o?t=805)

All of these issues were actually the main reason I started looking into Docker Stack and Docker

[13:30](https://youtu.be/fuZoxuBiL9o?t=810)

Swarm, as they have a much better approach when it comes to managing secrets. The Docker secret

[13:36](https://youtu.be/fuZoxuBiL9o?t=816)

command, this command will allow us to create the secret inside of our Docker host in a way that's

[13:40](https://youtu.be/fuZoxuBiL9o?t=820)

both encrypted at rest and encrypted during transit. To show this in action, let's quickly open up

[13:46](https://youtu.be/fuZoxuBiL9o?t=826)

the Docker compose YAML file and scroll down to where our database is defined. Here you can see

[13:52](https://youtu.be/fuZoxuBiL9o?t=832)

I've been kind of naughty. As I've set the database password in both the web application and my

[13:57](https://youtu.be/fuZoxuBiL9o?t=837)

database service as an environment variable, shame on me. Let's go ahead and change this to instead

[14:02](https://youtu.be/fuZoxuBiL9o?t=842)

use a Docker secret. To do so, let's first create a new secret using the Docker secret create command.

[14:09](https://youtu.be/fuZoxuBiL9o?t=849)

The first argument of this command is the name of the secret that we want to create, which in my

[14:14](https://youtu.be/fuZoxuBiL9o?t=854)

case is going to be DB-password. Then we need to specify the actual secrets value itself.

[14:21](https://youtu.be/fuZoxuBiL9o?t=861)

As I mentioned before, Docker secret is very secure, so we can't just enter in the value of the

[14:26](https://youtu.be/fuZoxuBiL9o?t=866)

secret that we want to create. Instead, we need to either load this in from a file or load this

[14:31](https://youtu.be/fuZoxuBiL9o?t=871)

in through the standard input using just a dash. To add a secret via SDD in, you can use something

[14:38](https://youtu.be/fuZoxuBiL9o?t=878)

such as the printf command when it comes to macOS or Linux, piping this into the Docker secret

[14:43](https://youtu.be/fuZoxuBiL9o?t=883)

command as follows. When I go ahead and execute this command, it will then return the ID of the

[14:48](https://youtu.be/fuZoxuBiL9o?t=888)

created secrets, which we can also view if we run the Docker secret LS command. One thing to note

[14:54](https://youtu.be/fuZoxuBiL9o?t=894)

is that this secret is now secret. There's no way for us to retrieve this from Docker. For example,

[15:01](https://youtu.be/fuZoxuBiL9o?t=901)

if I run the Docker secret inspect command, you can see it gives us a bunch of information about

[15:06](https://youtu.be/fuZoxuBiL9o?t=906)

the secrets, but not the actual secret value itself. This is a good thing when it comes to security,

[15:11](https://youtu.be/fuZoxuBiL9o?t=911)

but you'll want to make sure that you're securely keeping the secret somewhere else as well.

[15:15](https://youtu.be/fuZoxuBiL9o?t=915)

With our secret deployed, we can now use it similar to how we would with Docker compose.

[15:20](https://youtu.be/fuZoxuBiL9o?t=920)

However, rather than setting the secret as a file, instead we define it as external.

[15:26](https://youtu.be/fuZoxuBiL9o?t=926)

Then in order to use this secret, it's pretty much the same as if we were using Docker compose,

[15:30](https://youtu.be/fuZoxuBiL9o?t=930)

adding it to the relevant services that need access to it, and then setting it in the associated

[15:35](https://youtu.be/fuZoxuBiL9o?t=935)

environment variables. When it comes to the database, this is the postgres password file environment

[15:40](https://youtu.be/fuZoxuBiL9o?t=940)

variable, which needs to be set to /run/secrets/db-password. Then when it comes to my web application,

[15:48](https://youtu.be/fuZoxuBiL9o?t=948)

I've created the same environment variable that we can use, which will load the secret from this

[15:52](https://youtu.be/fuZoxuBiL9o?t=952)

file. Now, when I go to run this code, we can see that our database redeploys, and our application

[15:58](https://youtu.be/fuZoxuBiL9o?t=958)

is up and running. Sort of. Actually, it's not. The database itself is working fine, but if I

[16:05](https://youtu.be/fuZoxuBiL9o?t=965)

go ahead and run Docker PS, you can see that the new version of the web application is actually failing.

[16:10](https://youtu.be/fuZoxuBiL9o?t=970)

This is because I'm accidentally using an old image version that doesn't have the database

[16:15](https://youtu.be/fuZoxuBiL9o?t=975)

password file environment variable set up, so it's unable to connect to the database and exiting

[16:20](https://youtu.be/fuZoxuBiL9o?t=980)

early. However, you'll notice that if I open up a web browser and head on over to my application,

[16:25](https://youtu.be/fuZoxuBiL9o?t=985)

it's still running. This is because Docker Stack has support for rolling releases,

[16:31](https://youtu.be/fuZoxuBiL9o?t=991)

which means it's still running the old configuration on my application that works,

[16:35](https://youtu.be/fuZoxuBiL9o?t=995)

whilst it tries to spin up a new instance in order to switch over the traffic. It basically acts

[16:40](https://youtu.be/fuZoxuBiL9o?t=1000)

as a very simple blue green deployment, but it's out of the box. This behavior is configured using

[16:46](https://youtu.be/fuZoxuBiL9o?t=1006)

the following three lines, setting the start-first value of the deployment upgrade order configuration.

[16:52](https://youtu.be/fuZoxuBiL9o?t=1012)

Personally, I think this is a great option to enable, as it allows you to have rolling releases

[16:56](https://youtu.be/fuZoxuBiL9o?t=1016)

when it comes to upgrading your production ready services, which is especially important if you

[17:02](https://youtu.be/fuZoxuBiL9o?t=1022)

have automated deployments. Let's go ahead and quickly fix this deployment by changing the image tag

[17:08](https://youtu.be/fuZoxuBiL9o?t=1028)

to one that supports the DB password file environment variable. Then I'm able to redeploy it using

[17:13](https://youtu.be/fuZoxuBiL9o?t=1033)

the Docker Stack Deploy command. Now when I go ahead and check this service, we can see that it's

[17:18](https://youtu.be/fuZoxuBiL9o?t=1038)

running successfully. One thing to note is that whilst this start-first configuration is available

[17:23](https://youtu.be/fuZoxuBiL9o?t=1043)

in the Docker Compose specification, it doesn't actually work when you use it with Docker Compose,

[17:28](https://youtu.be/fuZoxuBiL9o?t=1048)

or at least it didn't when I tried it. This is because both the Docker Compose specification and

[17:34](https://youtu.be/fuZoxuBiL9o?t=1054)

Docker Stack specification are shared, which means there are documented configuration options that

[17:39](https://youtu.be/fuZoxuBiL9o?t=1059)

either one or the other don't support. For example, Docker Stack when it comes to the build configuration,

[17:45](https://youtu.be/fuZoxuBiL9o?t=1065)

and Docker Compose with the start-first update ordering. In fact, another feature that Docker

[17:50](https://youtu.be/fuZoxuBiL9o?t=1070)

Compose doesn't have support for is built in load balancing, which both Docker Stack and Docker

[17:56](https://youtu.be/fuZoxuBiL9o?t=1076)

Swarm do. To show this in action, let me first scale up the web application to three replicas,

[18:02](https://youtu.be/fuZoxuBiL9o?t=1082)

using the Docker Service Scale command. Next, if I go ahead and tail the logs using the following

[18:07](https://youtu.be/fuZoxuBiL9o?t=1087)

Docker Service Logs command using the Dash F flag, you can see that the built-in load balancer is

[18:13](https://youtu.be/fuZoxuBiL9o?t=1093)

distributing these requests against each replica in a round robin way. Whilst you are able to scale

[18:19](https://youtu.be/fuZoxuBiL9o?t=1099)

up replicas when it comes to Docker Compose, you're only able to bind a single instance on a

[18:23](https://youtu.be/fuZoxuBiL9o?t=1103)

given port. This means in order to effectively use load balancing, you need to use an external

[18:28](https://youtu.be/fuZoxuBiL9o?t=1108)

proxy such as traffic or nginx. Now, to be fair, when it comes to my own production services,

[18:35](https://youtu.be/fuZoxuBiL9o?t=1115)

I actually still make use of traffic in order to perform load balancing, mainly because it provides

[18:40](https://youtu.be/fuZoxuBiL9o?t=1120)

the ability for HDDPS and does a better job at forwarding client IPs. This is typically what my

[18:46](https://youtu.be/fuZoxuBiL9o?t=1126)

traffic implementation looks like, which sets up load balancing from my web service and automatically

[18:52](https://youtu.be/fuZoxuBiL9o?t=1132)

generates certs as well. As I just mentioned, there is one issue that I found when using Docker Swarm.

[18:58](https://youtu.be/fuZoxuBiL9o?t=1138)

Because of the way that Docker Compose Handlers load balancing, it prevents the original client IP

[19:02](https://youtu.be/fuZoxuBiL9o?t=1142)

from being forwarded to your services. For some situations, this is pretty annoying, and given by

[19:08](https://youtu.be/fuZoxuBiL9o?t=1148)

the length of this GitHub issue, a number of other people have also encountered. There is, however,

[19:13](https://youtu.be/fuZoxuBiL9o?t=1153)

an unofficial solution called Docker Ingress Routing Demon, which is used in production by a few

[19:19](https://youtu.be/fuZoxuBiL9o?t=1159)

companies to solve this problem. I want to take a look at how well this solution works in another

[19:24](https://youtu.be/fuZoxuBiL9o?t=1164)

video, probably when I take a look at clustering with Docker Swarm. In any case, when it comes to my

[19:29](https://youtu.be/fuZoxuBiL9o?t=1169)

own personal needs, using a load balancer such as traffic works pretty well. As I mentioned at the

[19:34](https://youtu.be/fuZoxuBiL9o?t=1174)

start of this video, another production ready feature that Swarm provides is the ability to

[19:38](https://youtu.be/fuZoxuBiL9o?t=1178)

roll back a service to a previous deployment. This is useful in the event where a bug is deployed,

[19:44](https://youtu.be/fuZoxuBiL9o?t=1184)

but isn't severe enough to fail the health check. To show this in action, if I go ahead and change

[19:48](https://youtu.be/fuZoxuBiL9o?t=1188)

the image of this deployment to be one called Broken Quote, followed by then deploying it.

[19:54](https://youtu.be/fuZoxuBiL9o?t=1194)

When I open up a web browser, you can see that the quote feature of my web app is broken,

[19:58](https://youtu.be/fuZoxuBiL9o?t=1198)

as the name implies. Fortunately, I'm able to roll this back pretty easily by using the Docker

[20:03](https://youtu.be/fuZoxuBiL9o?t=1203)

service rollback command, passing in the name of the service that I want to roll back. Now, if I

[20:09](https://youtu.be/fuZoxuBiL9o?t=1209)

open up my web application again, you can see that the quotes are now fixed. That covers the basic

[20:14](https://youtu.be/fuZoxuBiL9o?t=1214)

overview of how I use Docker Stack with my applications on a VPS. However, there's one last thing

[20:20](https://youtu.be/fuZoxuBiL9o?t=1220)

that I think is worth showcasing, which is how I use it for automated deployments using GitHub

[20:25](https://youtu.be/fuZoxuBiL9o?t=1225)

actions. To do so, let's take a look at the pipeline workflow file found inside of my guest book

[20:30](https://youtu.be/fuZoxuBiL9o?t=1230)

web app, where I have automated deployments set up. Here, you can see that I have the two same

[20:36](https://youtu.be/fuZoxuBiL9o?t=1236)

jobs that we saw before in order to test and build and push a Docker image. In addition to these,

[20:42](https://youtu.be/fuZoxuBiL9o?t=1242)

I also have another job called deploy, which is where the actual Docker Stack deployment takes place.

[20:48](https://youtu.be/fuZoxuBiL9o?t=1248)

Let's go ahead and add this exact same job into my ZenStats project. Here, you'll notice that I'm

[20:53](https://youtu.be/fuZoxuBiL9o?t=1253)

defining the build and push step in the needs field, which means it's required to pass in order for

[20:58](https://youtu.be/fuZoxuBiL9o?t=1258)

this job to run. Then for the actual steps themselves inside of this job, there are two. The first is

[21:04](https://youtu.be/fuZoxuBiL9o?t=1264)

to check out the code at the current commit, which is pretty standard in GitHub actions. The second,

[21:09](https://youtu.be/fuZoxuBiL9o?t=1269)

however, is a third-party action to deploy the Docker Stack. You can find the documentation for this

[21:14](https://youtu.be/fuZoxuBiL9o?t=1274)

action on the GitHub actions marketplace, which provides a full list of the inputs that you can set.

[21:20](https://youtu.be/fuZoxuBiL9o?t=1280)

Let's go ahead and take a look at these values whilst I configure it for the ZenFold.site.

[21:25](https://youtu.be/fuZoxuBiL9o?t=1285)

First of all, let's go ahead and change the name of the stack from GEST book to ZenFold.site.

[21:30](https://youtu.be/fuZoxuBiL9o?t=1290)

Next, you'll notice for the file property, this is actually set to docker-stack.yaml.

[21:35](https://youtu.be/fuZoxuBiL9o?t=1295)

This file name is commonly used to differentiate between a Docker Compose configuration and a Docker Stack

[21:41](https://youtu.be/fuZoxuBiL9o?t=1301)

configuration. This, to me, seems like a pretty good idea, so I'm going to go ahead and rename my Docker

[21:47](https://youtu.be/fuZoxuBiL9o?t=1307)

Compose file to be docker-stack.yaml. Underneath the file value, we then have the host name for our Docker

[21:53](https://youtu.be/fuZoxuBiL9o?t=1313)

Stack deploy, which I'm going to change to be ZenFold.site. Underneath this, we have our remaining two

[21:59](https://youtu.be/fuZoxuBiL9o?t=1319)

values, the first of which is a user named deploy, and the second is an SSH private key, which is set

[22:06](https://youtu.be/fuZoxuBiL9o?t=1326)

to a GitHub secret. In order for this to work, we need to set both of these up inside of our VPS.

[22:12](https://youtu.be/fuZoxuBiL9o?t=1332)

So let's take a look at how we can do this securely. First of all, we need to create a new user on our

[22:17](https://youtu.be/fuZoxuBiL9o?t=1337)

VPS. The reason I prefer to create a new user for deployments is so that I can easily limit the

[22:23](https://youtu.be/fuZoxuBiL9o?t=1343)

permissions this user has. This is a good security measure to limit the amount of damage if the SSH

[22:29](https://youtu.be/fuZoxuBiL9o?t=1349)

private key happens to be compromised. We can add a new user to this VPS by using the following add

[22:34](https://youtu.be/fuZoxuBiL9o?t=1354)

user command, setting the user's name. In my case, I like to use the name of deploy when it comes

[22:40](https://youtu.be/fuZoxuBiL9o?t=1360)

to my deployment users. Then with the user created, the next thing to do is to add them to the Docker

[22:45](https://youtu.be/fuZoxuBiL9o?t=1365)

group using the following user mod command. This will allow them to perform any Docker actions without

[22:50](https://youtu.be/fuZoxuBiL9o?t=1370)

needing elevated privileges from using pseudo. Next, we then need to create an SSH key pair for this

[22:56](https://youtu.be/fuZoxuBiL9o?t=1376)

user. This is achieved by using the following SSH key gen command. You'll notice that I'm doing

[23:02](https://youtu.be/fuZoxuBiL9o?t=1382)

this on my local machine rather than using the VPS. Once the key pair has been created, it should

[23:07](https://youtu.be/fuZoxuBiL9o?t=1387)

generate two files, one being our private key and the second being our public. Let's go ahead and

[23:13](https://youtu.be/fuZoxuBiL9o?t=1393)

add this public key into our user's authorized keys. To do so, first change into the new user on the

[23:18](https://youtu.be/fuZoxuBiL9o?t=1398)

VPS using the Sue command, entering in the user's password. Afterwards, we can then create the .ssh folder

[23:25](https://youtu.be/fuZoxuBiL9o?t=1405)

inside of their home directory using the following make-deer command. Then in order to add the SSH

[23:30](https://youtu.be/fuZoxuBiL9o?t=1410)

public key to their authorized keys, copy it to your clipboard and then run the following command

[23:35](https://youtu.be/fuZoxuBiL9o?t=1415)

to paste it into the file. With that, we should now be able to SSH into this machine as our deploy

[23:40](https://youtu.be/fuZoxuBiL9o?t=1420)

user, which we can test using the following command. Next, we then want to restrict what commands

[23:45](https://youtu.be/fuZoxuBiL9o?t=1425)

this user can actually perform via SSH. This is another good security measure, which again will

[23:51](https://youtu.be/fuZoxuBiL9o?t=1431)

reduce the amount of damage if the SSH key is accidentally compromised. To do so, open up the

[23:57](https://youtu.be/fuZoxuBiL9o?t=1437)

authorized keys file that we just created and add in the following text before the actual key itself.

[24:03](https://youtu.be/fuZoxuBiL9o?t=1443)

This will restrict the user to only being able to perform the Docker Stack deploy command when using

[24:08](https://youtu.be/fuZoxuBiL9o?t=1448)

SSH with this key. Now we can test that this is the case by attempting to SSH in as our deploy user,

[24:14](https://youtu.be/fuZoxuBiL9o?t=1454)

which should be rejected. However, when I go to run the Docker Stack deploy command,

[24:19](https://youtu.be/fuZoxuBiL9o?t=1459)

this one should work. With that, we're now ready to add the private key to our GitHub repository.

[24:24](https://youtu.be/fuZoxuBiL9o?t=1464)

To do so, navigate over to the actions secrets page found inside of the repo settings.

[24:29](https://youtu.be/fuZoxuBiL9o?t=1469)

Then, in sub of this page, click the big green new repository secret button, which will bring us

[24:35](https://youtu.be/fuZoxuBiL9o?t=1475)

to a form we can create a secret with. Here, you'll want to set the name of this to be the same

[24:39](https://youtu.be/fuZoxuBiL9o?t=1479)

value as defined in the GitHub action, which in my case is deploy SSH private key. Then, for the

[24:46](https://youtu.be/fuZoxuBiL9o?t=1486)

actual secret value itself, go ahead and paste in the contents of the private key before saving

[24:51](https://youtu.be/fuZoxuBiL9o?t=1491)

our secret. Now, if I go ahead and commit my code followed by pushing it up, when I navigate over

[24:56](https://youtu.be/fuZoxuBiL9o?t=1496)

to my GitHub repo, we should see the deployments start to work with the deploy job, and it completes

[25:01](https://youtu.be/fuZoxuBiL9o?t=1501)

successfully. With that, our automated deployment is already set up. However, there's one last thing

[25:06](https://youtu.be/fuZoxuBiL9o?t=1506)

I like to do, which is to specify which image to use when it comes to deployments. If you remember,

[25:12](https://youtu.be/fuZoxuBiL9o?t=1512)

for each image that we build in this pipeline, we're tagging it with both the latest tag and the

[25:17](https://youtu.be/fuZoxuBiL9o?t=1517)

gikmid hash of the code that this image is built off. So, in order to make our deployments more

[25:22](https://youtu.be/fuZoxuBiL9o?t=1522)

deterministic, we want to make sure to use this same image tag. To achieve this, we can use an

[25:27](https://youtu.be/fuZoxuBiL9o?t=1527)

environment variable, replacing the reference to our Docker image tag in our compose yaml with the

[25:32](https://youtu.be/fuZoxuBiL9o?t=1532)

following syntax, which will cause it to be loaded from an environment variable named gikmid hash.

[25:38](https://youtu.be/fuZoxuBiL9o?t=1538)

If I go ahead and set this environment variable to the last images hash and run the Docker stack

[25:43](https://youtu.be/fuZoxuBiL9o?t=1543)

deploy command, we should see our service deployed with the image hash we specified. In addition to

[25:48](https://youtu.be/fuZoxuBiL9o?t=1548)

this, we can also specify a default value for this environment variable in the case that it's not set.

[25:54](https://youtu.be/fuZoxuBiL9o?t=1554)

This is done using the following syntax, which in this case will set the default value of the

[25:59](https://youtu.be/fuZoxuBiL9o?t=1559)

environment variable to be latest. With that, the last thing to do is to set this environment variable

[26:04](https://youtu.be/fuZoxuBiL9o?t=1564)

in our deployment pipeline. This is done by setting the EMV file option in the stack deploy action.

[26:10](https://youtu.be/fuZoxuBiL9o?t=1570)

Then we can go ahead and create this EMV file using a step before this one. Here, we're creating a

[26:15](https://youtu.be/fuZoxuBiL9o?t=1575)

file with a gikmid hash environment variable set to the current github_shar_value. Now, if I commit and

[26:21](https://youtu.be/fuZoxuBiL9o?t=1581)

push up this code, we should see the pipeline working without issue. And we can test that it's using

[26:26](https://youtu.be/fuZoxuBiL9o?t=1586)

the correct image by making the following code change to the page title, committing it and

[26:31](https://youtu.be/fuZoxuBiL9o?t=1591)

pushing it to the github repo. Then once the pipeline completes, if I check out my deployed

[26:35](https://youtu.be/fuZoxuBiL9o?t=1595)

web application, we can see it's now running the new version with the updated title.

[26:40](https://youtu.be/fuZoxuBiL9o?t=1600)

With that, we've covered the basics of how I use Docker stack when it comes to deploying on a VPS,

[26:45](https://youtu.be/fuZoxuBiL9o?t=1605)

including how I have it set up for automated deployments. Personally, as somebody who has come from

[26:50](https://youtu.be/fuZoxuBiL9o?t=1610)

mostly working with Kubernetes, I've been impressed with how lightweight yet functional Docker stack has been.

[26:56](https://youtu.be/fuZoxuBiL9o?t=1616)

Whilst it's certainly not perfect and does come with its own caveats, so far, I found it to be a

[27:02](https://youtu.be/fuZoxuBiL9o?t=1622)

really good solution when it comes to running my own applications. One thing I'm still yet to try

[27:07](https://youtu.be/fuZoxuBiL9o?t=1627)

is setting this up to work as a cluster. But given how easy everything else has been,

[27:12](https://youtu.be/fuZoxuBiL9o?t=1632)

I don't expect this to be too difficult. However, that's going to be a video for another time.

[27:17](https://youtu.be/fuZoxuBiL9o?t=1637)

So if you're interested, then please let me know in the comments down below. Otherwise,

[27:20](https://youtu.be/fuZoxuBiL9o?t=1640)

I want to give a big thank you to Hostinger for sponsoring this video. If you're interested in

[27:25](https://youtu.be/fuZoxuBiL9o?t=1645)

obtaining your own VPS instance for a super low price, then either visit the link in the description

[27:30](https://youtu.be/fuZoxuBiL9o?t=1650)

down below or head on over to Hostinger.com/dreamsofcode and make sure to use my coupon code "Dreams

[27:36](https://youtu.be/fuZoxuBiL9o?t=1656)

of Code" when you check out. Otherwise, I want to give a big thank you for watching and I'll see you

[27:41](https://youtu.be/fuZoxuBiL9o?t=1661)

on the next one.

