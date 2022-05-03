import uuid

def create():
    return PipelineDB(InMemoryObjectStore())

class InMemoryObjectStore:

    def __init__(self):
        self.objects = {}

    async def create_object(self, contents, name=None):
        if name is None:
            name = uuid.uuid4().hex
        self.objects[name] = contents
        return name

    async def modify_object(self, name, fn):
        fn(self.objects[name])
        return self.objects[name]

    async def read_object(self, name):
        return self.objects[name]

class PipelineDB:

    def __init__(self, store):
        self.store = store

    async def init(self):
        await self.store.create_object({"pipelines": {}}, "index")

    async def store_pipelines(self, pipelines):
        return [
            await self.store_pipeline(pipeline[1]["name"], pipeline[2:])
            for pipeline in pipelines
        ]

    async def get_active_pipelines(self):
        active_pipelines = []
        index = await self.store.read_object("index")
        for pipeline_id in index["pipelines"].values():
            pipeline = await self.store.read_object(pipeline_id)
            active_id = pipeline["versions"][0]
            active_pipeline = await self.store.read_object(active_id)
            active_pipelines.append((active_id, active_pipeline))
        return active_pipelines

    async def store_execution(self, pipeline_id, execution):
        execution_id = await self.store.create_object(execution)
        await self.store.modify_object(pipeline_id, lambda pipeline:
            pipeline["execution_ids"].append(execution_id)
        )
        return execution_id

    async def modify_execution_done(self, execution_id):
        def modify(execution):
            execution["status"] = "done"
        return await self.store.modify_object(execution_id, modify)

    async def modify_execution_start(self, execution_id, stage_id, args):
        def modify(execution):
            execution["stages"][stage_id]["status"] = "running"
            execution["stages"][stage_id]["input"] = args
        return await self.store.modify_object(execution_id, modify)

    async def add_log(self, logs_id, line):
        def modify(logs):
            logs["lines"].append(line)
        return await self.store.modify_object(logs_id, modify)

    async def store_logs(self, logs):
        return await self.store.create_object(logs)

    async def get_logs(self, logs_id):
        return await self.store.read_object(logs_id)

    async def get_pipeline(self, pipeline_id):
        return await self.store.read_object(pipeline_id)

    async def get_pipelines(self):
        return [
            {
                "id": key,
                "display_name": key,
            }
            for key, value
            in (await self.store.read_object("index"))["pipelines"].items()
        ]

    async def get_execution(self, execution_id):
        return await self.store.read_object(execution_id)

    async def store_pipeline(self, name, pipeline):
        pipeline_id = await self.store.create_object({
            "definition": pipeline,
            "execution_ids": []
        })
        foo = await self.store.create_object({"versions": [pipeline_id]})
        await self.store.modify_object("index", lambda index:
            index["pipelines"].__setitem__(
                "name",
                foo
            )
        )
        return pipeline_id
