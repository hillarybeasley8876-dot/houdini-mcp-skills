"""Read-only MCP checks. --scene also reads the live Houdini scene."""
import argparse, asyncio, json, sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=Path(__file__).resolve().parent

async def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port',type=int,default=9877)
    ap.add_argument('--scene',action='store_true')
    args=ap.parse_args()
    bridge=ROOT/'houdini-mcp/scripts/python/houdinimcp/houdini_mcp_server.py'
    params=StdioServerParameters(command=sys.executable,args=[str(bridge),'--port',str(args.port)])
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            initialized=await asyncio.wait_for(session.initialize(),30)
            listed=await asyncio.wait_for(session.list_tools(),30)
            names=[tool.name for tool in listed.tools]
            assert len(names)==25, f'Expected 25 tools, got {len(names)}'
            assert 'get_scene_info' in names and 'execute_houdini_code' in names
            report={'handshake':'PASS','tools':len(names),'server':initialized.serverInfo.name,'scene':'NOT_REQUESTED'}
            if args.scene:
                result=await asyncio.wait_for(session.call_tool('get_scene_info',{}),30)
                assert not result.isError, 'Houdini tool returned an MCP error'
                payload=json.loads('\n'.join(item.text for item in result.content if item.type=='text'))
                assert isinstance(payload,dict) and 'error' not in payload and payload.get('status')!='error', 'Houdini scene read failed'
                report['scene']='PASS'
            print(json.dumps(report,indent=2))

if __name__=='__main__':
    asyncio.run(main())
