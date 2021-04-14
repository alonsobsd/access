import itertools
import copy

from aiohttp import web
from aiohttp_jinja2 import template

from app.objects.secondclass.c_fact import Fact
from app.service.auth_svc import for_all_public_methods, check_authorization


@for_all_public_methods(check_authorization)
class AccessApi:

    def __init__(self, services):
        self.data_svc = services.get('data_svc')
        self.rest_svc = services.get('rest_svc')
        self.auth_svc = services.get('auth_svc')

    @template('access.html')
    async def landing(self, request):
        search = dict(access=tuple(await self.auth_svc.get_permissions(request)))
        abilities = await self.data_svc.locate('abilities', match=search)
        tactics = sorted(list(set(a.tactic.lower() for a in abilities)))
        obfuscators = [o.display for o in await self.data_svc.locate('obfuscators')]
        return dict(agents=[a.display for a in await self.data_svc.locate('agents', match=search)],
                    abilities=[a.display for a in abilities], tactics=tactics, obfuscators=obfuscators)

    async def exploit(self, request):
        data = dict(await request.json())
        converted_facts = [Fact(trait=f['trait'], value=f['value']) for f in data.get('facts', [])]
        await self.rest_svc.task_agent_with_ability(data['paw'], data['ability_id'], data['obfuscator'], converted_facts)
        return web.json_response('complete')

    async def abilities(self, request):
        search = dict(access=tuple(await self.auth_svc.get_permissions(request)))
        data = dict(await request.json())
        agent = (await self.data_svc.locate('agents', dict(paw=data['paw'])))[0]
        abilities = await self.data_svc.locate('abilities', match=search)
        capable_abilities = await agent.capabilities(list(itertools.chain.from_iterable(abilities)))
        return web.json_response([a.display for a in capable_abilities])

    async def executor(self, request):
        data = dict(await request.json())
        search = dict(access=tuple(await self.auth_svc.get_permissions(request)),
                      ability_id=data['ability_id'])
        agent = (await self.data_svc.locate('agents', dict(paw=data['paw'])))[0]
        abilities = await self.data_svc.locate('abilities', match=search)
        ability, executor = (await agent.capabilities_with_preference(abilities))[0]
        trimmed_ability = copy.deepcopy(ability)
        trimmed_ability.executors = [executor]
        return web.json_response(trimmed_ability.display)
