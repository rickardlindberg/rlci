An experimental CI/CD system designed to solve problems I've had with Jenkins.

## TODO

* Allow template for stage body
    * Store two kinds of templates: block | stageBody
* What should introduce a new scope? global/pipeline/template
* RLMeta
    * Syntax to capture location -> function that raises error at that location
    * `compile_chain` without `sys.exit`?
* Pipeline storage format
    * Store as AST?
        * AST can be turned into Graphviz
        * AST can be tutned into all sorts of other useful things
    * Is a diff in pipeline caused by different compilation acceptable?
      (Pipeline file the same, but the AST looks different (optimized,
      different structure))
    * ToDag -> ToGraph? ToPipelineASTS?
* Implement run_pipeline
    * python tool.py run_pipeline < echo "pipeline def"
* Implement pipeline server which manages
    * Pipeline executions
    * Locks
    * DB?
* Can we wait for port open instead of sleeping in server test?
