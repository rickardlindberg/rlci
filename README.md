# RLCI

**An experimental CI/CD system designed to suit my needs.**

**DEMO**: http://ci.rickardlindberg.me/

I have used [Jenkins](https://www.jenkins.io/) in many projects and I've had a
lot of success with it. However, over time I've also become more and more
frustrated with it, thinking that it is not the right tool for the job. It
feels like a patchwork of functionality that is difficult to get to work the
way I would like a CI/CD system to work.

## Vision

RLCI is an attempt to build a CI/CD system to suit my needs. What are my needs?
This is what I initially came up with:

* Ability to define flexible, **first-class pipelines**.
    * A pipeline defines a process. A change flows through a pipeline. (In
      Jenkins, a pipeline is run producing multiple pipeline runs.)
    * All steps should **run in isolation**. (In Jenkins, workspaces are
      reused, and one step can see the workspace used in another step.)
    * Pipelines should have a **visual representation**. (Jenkins can't show
      the whole pipeline until all steps have been run. If some steps at the
      end are run seldom, they will never be visualized.)
* Everything (pipelines/configuration/etc) is **written in code**. (In Jenkins,
  many things can be configured in the GUI which is a convenient way to start,
  but a pain in the long run.)
* Ability to re-rerun parts of a failed pipeline.
* Pipeline visualization:
    * Visualise as as a flow of commits passing through stages and gathering
      confidence.
    * Show statistics how long each stage takes and its failure rate.

## Notes

### Where should a pipeline be defined?

Jenkins and other CI/CD systems make us define the pipeline in the repo itself.
Does that make sense?

On the one hand, it ensures that the pipeline is always in sync with the repo.
If a build command changes, we can update the pipeline build step accordingly.

On the other hand, it doesn't feel right that the repo has knowledge of where
it is deployed for example.

A pipeline encodes a process for software delivery. The process and the code
can change independently.

**If things change together, they should be together. If not, they should
not.**

My current thinking is that the repo should expose an interface to the pipeline
for doing certain tasks. For example `./zero.py build` to build and test, and
`./zero.py deploy` to deploy the application somewhere. If the build
process changes, only a change to `zero.py` is needed, and the pipeline can
stay the same.

### Server requirements

This section documents requirements on the server that RLCI runs on. Currently
these requirements are not automated, but RLCI assumes that they are in place:

* SSH access (using keys) for user X

    # /etc/ssh/sshd_config
    PrintLastLog no
    PermitRootLogin no
    PasswordAuthentication no

* Directory `/opt/rlci` present with full permissions to user X
* Git configured with email/username
* Web server configured to serve static content from `/opt/rlci/html`

    # /etc/nginx/conf.d/rlci.conf
    server {
        listen       80;
        server_name  ci.rickardlindberg.me;
        location / {
            root         /opt/rlci/html;
        }
    }

* Software installed:
    * Python
    * Git

I'm currently not sure how/where to automate all of this, so that's why the
documentation exists instead. But hopefully, we can get rid of it.

## Development

I will practice agile software development in this project. Some guiding
principles:

* **What is the simplest thing that could possibly work?**
* **You ain't gonna need it! / Evolutionary design**
* **TDD / Refactoring**
    * Get it working as fast as possible, then refactor/design
* **Zero Friction Development**

## Stories

This is the backlog of stories to serve as a reminder of what might be
interesting to work on next.

* When I integrate my changes, and someone else is currently integrating, I
  have to wait for them to finish.

## History

This is where I document the completed stories.

### #1 Runs a hard-coded, pre-defined pipeline

*Running pipelines is the core function of the CI/CD server. If we can get it
to run a hard-coded, pre-defined pipeline, we have for sure demonstrated some
progress.*

I completed the main part of this story in a video. Watch me get all the
infrastructure in place to write a test for the very first version of RLCI.

**VIDEO:** [Rebooting RLCI with an agile approach using TDD and zero friction
development.](https://youtu.be/Re7litDdulU)

Browse the
[code](https://github.com/rickardlindberg/rlci/tree/w23-rlci-reboot-end) as it
looked like at the end of the video and look at the complete
[diff](https://github.com/rickardlindberg/rlci/compare/d3bda99f9d427865f9f1c2e394a5c7c392bcdc12...453ae3d26e70a2af1577ee4a06ae2001c8038606)
of changes.

After the video I did some
[refactoring](https://github.com/rickardlindberg/rlci/compare/e1c4c5c34b75856ca8e62ad172045778a3af8f63...d5bd857e66682ebdc5ad136d7b8270d7e3915961)
and made some more improvements to the build system:

* [Usage should exit with code 1.](https://github.com/rickardlindberg/rlci/commit/48a6c55fc2356718c49a080500ba81bf1c78ba88)
* [Exit with code 0 if tests fail.](https://github.com/rickardlindberg/rlci/commit/03a8a53e218f3c0de81be3e47d79b93f46428a57) (Should have been "code 1" in message.)
* [Update usage and inluce the build command.](https://github.com/rickardlindberg/rlci/commit/b39d5a5cffd359365223d591558d38fafc81ac30)

### #2 Extend hard coded pipeline to integrate a branch

*The hard coded pipeline currently does nothing. We could start fleshing out
this pipeline to be the pipeline that RLCI could use. The first step in that
pipeline should be to integrate a branch (merge with `main` and run tests and
promote if passed).*

I completed this story along with some clean up in a video.

**VIDEO:** [Adding continuous integration functionality to
RLCI.](https://youtu.be/sokSvnAkd5E)

Browse the
[code](https://github.com/rickardlindberg/rlci/tree/w24-extend-hard-coded-pipeline)
as it looked like at the end of the video and look at the complete
[diff](https://github.com/rickardlindberg/rlci/compare/745a36ef6e3ede7cf8b6b6643058a0baeb570d2d...w24-extend-hard-coded-pipeline)
of changes.

### #3 Extend hard coded pipeline to run in isolation

*This prevents multiple pipeline runs to interfere with each other via
contaminated workspaces.*

I completed this story in a video. Watch me do refactoring, internal
improvements, and finally adding functionality to execute pipelines in
isolation.

**VIDEO:** [Making RLCI pipelines run in
isolation.](https://youtu.be/0jJEPgomRCc)

Browse the
[code](https://github.com/rickardlindberg/rlci/tree/w25-pipeline-run-in-isolation)
as it looked like at the end of the video and look at the complete
[diff](https://github.com/rickardlindberg/rlci/compare/86e4bf72c35c4fb035fcc5caa58218684ccc06b4...w25-pipeline-run-in-isolation)
of changes.

#### Retro

I am not happy with how the design turned out. I'm not sure it will allow me to
move forward smoothly. I think I will spend some time researching
testing/design strategies applicable for me in this situation.

But can I do that without also working on a story?

I think adding more realistic output will require that I have a better design.
So perhaps I should try to refactor towards a design that will make reporting
easy to implement. And then implement that.

Overall, I think that much time needs to be spend on refactoring/design.
Perhaps this ratio is higher in the beginning of a project. I feel like 90/10
design/refactoring vs. implementing stories.

### #4 Make pipeline print to the terminal what it is doing

This story started out with a bunch of refactoring and design. I wasn't really
sure what story to work on when I started. I just knew I needed to clean up
some things before I could move on. Perhaps I should have done that in the
previous story already. Once I was happier with the design, it was quite
natural to extend the pipeline to report what it was doing, so that's what I
did.

Browse the
[code](https://github.com/rickardlindberg/rlci/tree/story-4-end)
as it looked like at the end of the story and look at the complete
[diff](https://github.com/rickardlindberg/rlci/compare/w25-pipeline-run-in-isolation...story-4-end)
of changes.

#### Retro

* The article [Favor real dependencies for unit
  testing](https://stackoverflow.blog/2022/01/03/favor-real-dependencies-for-unit-testing/)
  presented a solution to a design problem I was having. For more info, see
  [my video about it](https://youtu.be/d7fq8JyU9jg).

* Functional core, imperative shell. Hexagonal architecture. A-frame
  architecture. They are all similar. Thinking in terms of pure/IO Haskell
  functions made it pretty clear to me. I feel like RLCI is quite free from
  pure logic at this point. It is mostly stitching together infrastructure
  code. But I will keep it in mind and look for opportunities to extract pure
  functions.

* Evolutionary design is hard. What if the first step was in the wrong
  direction? At least a rewrite is not a rewrite of that much.

* I used the TDD principle of taking every shortcut possible to get a test
  passing, and then improved the design with refactoring. (When writing the new
  infrastructure wrapper `Process`.) It felt awkward to do ugly things, but I
  got to a clean solution faster.

* I caught myself having done some premature parametrization and [removed
  it](https://github.com/rickardlindberg/rlci/commit/185f184f0f1f477f5818bfa44e8803bc71dc727e).

* Tests have guided my design decision more than they have done in the past.
  Mainly in the way that I try to think about why writing a test is complicated
  and then changing the design to make testing simple.

### #5 More realistic environment (run RLCI on server)

*One purpose of a CI server is to provide the same environment for integration
builds. That requires the CI server to not run on my laptop. Create a dedicated
server to which RLCI can be deployed and run. (My CI-server is a Linode. My
pipeline is the RLCI program. Linode provides same environment / integration
point. RLCI provides process.)*

I implemented the main part of the functionality in a video:

**VIDEO:** [Deploying my continuous integration software to a server.](https://youtu.be/BmUz4my7eko)

Browse the
[code](https://github.com/rickardlindberg/rlci/tree/video-w27-end)
as it looked like at the end of the video and look at the complete
[diff](https://github.com/rickardlindberg/rlci/compare/video-w27-start...video-w27-end)
of changes.

When reviewing the work, I came up with the following list of refactorings and
improvements to work on before considering the story done:

* Second test case for no second argument to deploy
* Always delete temporary branch
* Integrate without commits?
* Diffs hard to read
* Assumes /opt/rlci exists
* Ugly tests. How to make them better?
* Don't execute zero.py through Shell? Missed failure of git checkout ''
* Clean up CI serer home folder

I worked on those in another video:

**VIDEO:** [Therapeutic refactoring and polishing of a
feature.](https://youtu.be/C05OD7h0-gg)

Browse the
[code](https://github.com/rickardlindberg/rlci/tree/video-w28-end)
as it looked like at the end of the video and look at the complete
[diff](https://github.com/rickardlindberg/rlci/compare/video-w28-start...video-w28-end)
of changes.

#### Retro

I feel like there is a tension between extending the codebase with new
functionality versus keeping it clean.

I am still not sure how to integrate refactoring and design into an agile
approach. It is supposed to be done in the background somehow while the main
focus is delivering stories.

### #6 Custom pipelines

*There is only one hard coded pipeline. Make it possible to define more and
trigger them from the CLI.*

I started this story by working on extracting a database class. I figured,
with a database, we can store multiple pipelines, and we can also store the
logs so that we can show history of pipeline runs.

I made a video about this process:

**VIDEO:** [I made a mistake when evolving the design of RLCI to support a
database.](https://youtu.be/WlvsjCeuT6w)

After working on the database for a while, I realized that I had designed it
too much up front.

I reverted the [speculative
changes](https://github.com/rickardlindberg/rlci/commit/44601aca04c11ba20f01d65b3b11ffd060217a45)
and instead committed to this story only.

The following tests prove that multiple pipelines can be triggered.

    >>> RLCIApp.run_in_test_mode(
    ...     args=["trigger", "rlci"]
    ... ).has("STDOUT", "Triggered RLCIPipeline")
    True

    >>> RLCIApp.run_in_test_mode(
    ...     args=["trigger", "test-pipeline"]
    ... ).has("STDOUT", "Triggered TEST-PIPELINE")
    True

We still have to define the pipelines in the source code. Eventually though we
should be able to store them in an external database instead. But that is for
another story.

Browse the
[code](https://github.com/rickardlindberg/rlci/tree/story-6-end)
as it looked like at the end of the story and look at the complete
[diff](https://github.com/rickardlindberg/rlci/compare/story-6-start...story-6-end)
of changes.

### #7 More realistic output

*The pipeline currently writes its "report" to stdout. I imagine the CI-server
having a web-front end to display its status. Therefore convert the stdout
report to a HTML-file that can be served by a web server.*

I made a video about the process of working on this story:

**VIDEO:** [I did the simplest thing that could possibly work. Here's what
happened.](https://youtu.be/BXyiqhqXT0U)

I did the absolute minimal and simple thing that could possible work. Many more
improvements can be made to the HTML report, but this is a first version.

Browse the
[code](https://github.com/rickardlindberg/rlci/tree/story-7-end)
as it looked like at the end of the story and look at the complete
[diff](https://github.com/rickardlindberg/rlci/compare/story-7-start...story-7-end)
of changes.

