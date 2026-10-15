#!/usr/bin/env python3
"""Regenerate the editable drawio sources and SVGs from the same layout.

Uses only Python's standard library. SVGs embed the matching drawio XML.
After editing a .drawio in diagrams.net, export SVG there (include diagram data);
to retain reproducibility, also update this layout before running this script.
"""

from pathlib import Path
import html
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
COLORS = {
    "app": ("#E8EDF3", "#F6F8FB"),
    "sdk": ("#DDEBFC", "#F2F7FE"),
    "catalog": ("#ECE4F9", "#F8F5FD"),
    "topo": ("#FFF0C7", "#FFFAEB"),
    "storage": ("#DDF1E1", "#F2FAF4"),
    "raft": ("#DDF1F2", "#F2FAFA"),
    "persist": ("#FBE6D6", "#FEF7F1"),
}
LINES = {"call": ("#526173", ""), "rpc": ("#245B9E", ""),
         "event": ("#245B9E", "7 5"), "disk": ("#A35421", "")}


class Diagram:
    def __init__(self, name, title, subtitle, width, height):
        self.name, self.title, self.subtitle = name, title, subtitle
        self.width, self.height = width, height
        self.groups, self.nodes, self.edges = [], [], []

    def group(self, id, x, y, w, h, title, color, parent=None, object=False):
        self.groups.append(dict(id=id, x=x, y=y, w=w, h=h, title=title,
                                color=color, parent=parent, object=object))

    def node(self, id, x, y, w, h, title, body="", color="app", parent=None):
        self.nodes.append(dict(id=id, x=x, y=y, w=w, h=h, title=title,
                               body=body, color=color, parent=parent))

    def edge(self, source, target, pts, label="", at=None, kind="call", both=False):
        self.edges.append(dict(source=source, target=target, pts=pts,
                               label=label, at=at, kind=kind, both=both))

    def render(self):
        # Containment and endpoint checks protect both editable and rendered output.
        all_nodes = {n["id"]: n for n in self.groups + self.nodes}
        assert len(all_nodes) == len(self.groups) + len(self.nodes)
        for n in self.groups + self.nodes:
            if n["parent"]:
                p = all_nodes[n["parent"]]
                assert p["x"] <= n["x"] and p["y"] + 42 <= n["y"]
                assert n["x"] + n["w"] <= p["x"] + p["w"]
                assert n["y"] + n["h"] <= p["y"] + p["h"]
        for e in self.edges:
            for a,b in zip(e['pts'],e['pts'][1:]):
                assert a[0] == b[0] or a[1] == b[1], (self.name,'non-orthogonal',e)
                for n in self.nodes:
                    if n['id'] in (e['source'],e['target']): continue
                    x1,x2=n['x'],n['x']+n['w'];y1,y2=n['y'],n['y']+n['h']
                    cross=(a[0]==b[0] and x1<a[0]<x2 and max(min(a[1],b[1]),y1)<min(max(a[1],b[1]),y2)) or (a[1]==b[1] and y1<a[1]<y2 and max(min(a[0],b[0]),x1)<min(max(a[0],b[0]),x2))
                    assert not cross,(self.name,'edge crosses unrelated node',e['source'],e['target'],n['id'])
        mxfile = ET.Element("mxfile", host="app.diagrams.net", version="24.7.17")
        diagram = ET.SubElement(mxfile, "diagram", name=self.title, id=self.name)
        model = ET.SubElement(diagram, "mxGraphModel", grid="1", gridSize="10",
                              page="1", pageScale="1", pageWidth=str(self.width),
                              pageHeight=str(self.height), math="0", shadow="0")
        root = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", id="0")
        ET.SubElement(root, "mxCell", id="1", parent="0")

        def cell(id, value, style, x, y, w, h, parent="1"):
            c = ET.SubElement(root, "mxCell", id=id, value=value, style=style,
                              vertex="1", parent=parent)
            ET.SubElement(c, "mxGeometry", x=str(x), y=str(y), width=str(w),
                          height=str(h), **{"as": "geometry"})

        textstyle = "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;"
        cell("title", self.title, textstyle + "fontSize=28;fontStyle=1;", 40, 20, self.width-80, 40)
        cell("subtitle", self.subtitle, textstyle + "fontSize=17;", 40, 65, self.width-80, 30)
        for n in self.groups + self.nodes:
            x, y = n["x"], n["y"]
            if n["parent"]:
                p = all_nodes[n["parent"]]
                x, y = x-p["x"], y-p["y"]
            fill, groupfill = COLORS[n["color"]]
            if "object" in n:
                style = f"swimlane;html=1;startSize=42;horizontal=1;rounded=0;fillColor={fill};swimlaneFillColor={groupfill};strokeColor=#A6B0BC;fontSize=20;fontStyle=1;align=left;spacingLeft=12;"
                if n["object"]:
                    style += "dashed=1;dashPattern=6 4;"
                value = html.escape(n["title"])
            else:
                style = f"rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor={fill};strokeColor=#A6B0BC;fontColor=#1C2B3A;fontSize=17;spacing=10;"
                value = "<b>" + html.escape(n["title"]).replace("\n", "<br>") + "</b>"
                if n["body"]:
                    value += "<br>" + html.escape(n["body"]).replace("\n", "<br>")
            cell(n["id"], value, style, x, y, n["w"], n["h"], n["parent"] or "1")
        for i, e in enumerate(self.edges):
            s, t = all_nodes[e["source"]], all_nodes[e["target"]]
            a, b = e["pts"][0], e["pts"][-1]
            for p, node in [(a, s), (b, t)]:
                assert node["x"] <= p[0] <= node["x"]+node["w"] and node["y"] <= p[1] <= node["y"]+node["h"], (self.name, e)
                assert p[0] in (node["x"],node["x"]+node["w"]) or p[1] in (node["y"],node["y"]+node["h"]), (self.name,e)
            color, dash = LINES[e["kind"]]
            style = f"edgeStyle=none;rounded=0;html=1;strokeColor={color};strokeWidth=2;endArrow=block;endFill=1;exitX={(a[0]-s['x'])/s['w']};exitY={(a[1]-s['y'])/s['h']};exitPerimeter=0;entryX={(b[0]-t['x'])/t['w']};entryY={(b[1]-t['y'])/t['h']};entryPerimeter=0;"
            if dash: style += "dashed=1;dashPattern=7 5;"
            if e["both"]: style += "startArrow=block;startFill=1;"
            c=ET.SubElement(root,"mxCell",id=f"edge{i}",style=style,edge="1",parent="1",source=e["source"],target=e["target"])
            g=ET.SubElement(c,"mxGeometry",relative="1",**{"as":"geometry"})
            ar=ET.SubElement(g,"Array",**{"as":"points"})
            for px,py in e["pts"][1:-1]: ET.SubElement(ar,"mxPoint",x=str(px),y=str(py))
            if e["label"]:
                lx,ly=e["at"]
                lines=e["label"].split("\n")
                lw=max(text_width(v,15) for v in lines)+16
                lh=len(lines)*20+8
                cell(f"label{i}",html.escape(e["label"]).replace("\n","<br>"),textstyle+"fillColor=#FFFFFF;fontSize=15;align=center;",lx-lw/2,ly-lh/2,lw,lh)
        footer="组件颜色：SDK 蓝 / Catalog 紫 / Topo 黄 / Storage 绿 / Raft 青 / 持久化橙"
        cell("legend",footer,textstyle+"fontSize=16;",40,self.height-72,self.width-80,25)
        cell("legend2","连线标签：gRPC = 跨进程；调用 = 进程内；虚线 = 队列/事件回调；磁盘 = 文件读写",textstyle+"fontSize=16;",40,self.height-42,self.width-80,25)
        xml=ET.tostring(mxfile,encoding="unicode")
        (OUT / f"{self.name}.drawio").write_text(xml+"\n")

        svg=ET.Element("svg",xmlns="http://www.w3.org/2000/svg",width=str(self.width),height=str(self.height),viewBox=f"0 0 {self.width} {self.height}",content=xml,role="img",**{"aria-labelledby":"diagram-title diagram-desc"})
        ET.SubElement(svg,"title",id="diagram-title").text=self.title
        ET.SubElement(svg,"desc",id="diagram-desc").text=self.subtitle
        ET.SubElement(svg,"rect",width=str(self.width),height=str(self.height),fill="#FFFFFF")
        defs=ET.SubElement(svg,"defs")
        for kind,(color,_) in LINES.items():
            m=ET.SubElement(defs,"marker",id=f"arrow-{kind}",viewBox="0 0 10 10",refX="9",refY="5",markerWidth="7",markerHeight="7",orient="auto-start-reverse")
            ET.SubElement(m,"path",d="M 0 0 L 10 5 L 0 10 z",fill=color)
        def text(x,y,value,size=17,bold=False,anchor="middle"):
            el=ET.SubElement(svg,"text",x=str(x),y=str(y),fill="#1C2B3A",**{"font-family":"Arial, PingFang SC, Microsoft YaHei, sans-serif","font-size":str(size),"font-weight":"600" if bold else "400","text-anchor":anchor})
            el.text=value
        text(40,48,self.title,28,True,"start")
        text(40,85,self.subtitle,17,False,"start")
        for n in self.groups:
            fill,gfill=COLORS[n["color"]]
            attrs=dict(x=str(n["x"]),y=str(n["y"]),width=str(n["w"]),height=str(n["h"]),fill=gfill,stroke="#A6B0BC")
            if n["object"]:attrs["stroke-dasharray"]="6 4"
            ET.SubElement(svg,"rect",**attrs)
            ET.SubElement(svg,"rect",x=str(n["x"]),y=str(n["y"]),width=str(n["w"]),height="42",fill=fill)
            text(n["x"]+14,n["y"]+28,n["title"],20,True,"start")
        for e in self.edges:
            color,dash=LINES[e["kind"]]
            attrs={"points":" ".join(f"{x},{y}" for x,y in e["pts"]),"fill":"none","stroke":color,"stroke-width":"2","stroke-linejoin":"round","marker-end":f"url(#arrow-{e['kind']})"}
            if dash:attrs["stroke-dasharray"]=dash
            if e["both"]:attrs["marker-start"]=f"url(#arrow-{e['kind']})"
            ET.SubElement(svg,"polyline",**attrs)
        for n in self.nodes:
            fill,_=COLORS[n["color"]]
            ET.SubElement(svg,"rect",x=str(n["x"]),y=str(n["y"]),width=str(n["w"]),height=str(n["h"]),rx="7",fill=fill,stroke="#A6B0BC")
            title=n["title"].split("\n"); body=n["body"].split("\n") if n["body"] else []
            assert all(text_width(v,18) < n['w']-16 for v in title), (self.name,n['id'],'title width')
            assert all(text_width(v,16) < n['w']-16 for v in body), (self.name,n['id'],'body width')
            assert (len(title)+len(body))*24 < n['h'], (self.name,n['id'],'text height')
            y=n['y']+n['h']/2-(len(title)+len(body)-1)*12+6
            for line in title:text(n['x']+n['w']/2,y,line,18,True);y+=24
            for line in body:text(n['x']+n['w']/2,y,line,16);y+=24
        for e in self.edges:
            if not e['label']:continue
            x,y=e['at'];lines=e['label'].split('\n');w=max(text_width(v,15) for v in lines)+16;h=len(lines)*20+8
            ET.SubElement(svg,'rect',x=str(x-w/2),y=str(y-h/2),width=str(w),height=str(h),rx='3',fill='#FFFFFF',**{'fill-opacity':'0.97'})
            for j,line in enumerate(lines):text(x,y-(len(lines)-1)*10+j*20+5,line,15)
        text(40,self.height-55,footer,16,False,'start')
        text(40,self.height-25,"连线标签：gRPC = 跨进程；调用 = 进程内；虚线 = 队列/事件回调；磁盘 = 文件读写",16,False,'start')
        ET.ElementTree(svg).write(OUT/f"{self.name}.svg",encoding='utf-8',xml_declaration=True)


def text_width(s,size):
    return sum(1 if ord(c)>255 else 0.56 for c in s)*size


def cluster():
    d=Diagram('01-cluster','01｜集群总架构','一个 shard 的三副本示例；Catalog / Topo 当前单进程；端口来自本地 demo 配置，可修改。',1700,1250)
    d.group('app',40,130,500,230,'应用进程','sdk')
    d.node('cli',65,200,190,110,'CLI / 应用','DDL 调用方','app','app')
    d.node('sdk',300,200,210,110,'KVClient / SDK','路由、重试、幂等 ID','sdk','app')
    d.group('catalog',620,130,380,230,'Catalog 进程 · :50048','catalog')
    d.node('ddl',650,200,320,110,'CatalogService','库表定义 / DDL 状态','catalog','catalog')
    d.group('topo',1080,130,570,230,'Topo 进程 · :50049','topo')
    d.node('topoapi',1110,200,510,110,'TopoService','表规格、节点、副本组、路由','topo','topo')
    d.edge('cli','ddl',[(160,310),(160,390),(570,390),(570,225),(650,225)],'gRPC：建库 / 建表 / 改副本',(400,390),'rpc')
    d.edge('ddl','topoapi',[(970,255),(1110,255)],'gRPC：表规格',(1040,220),'rpc')
    d.edge('sdk','topoapi',[(405,200),(405,110),(1390,110),(1390,200)],'gRPC：GetTableRoutes（缓存刷新时）',(900,110),'rpc')
    for i,x in enumerate([40,610,1180]):
        p=f's{i}';d.group(p,x,640,480,510,f'Storage {i+1} 进程 · :{50051+i}','storage')
        d.node(p+'agent',x+35,710,410,90,'NodeAgent','RegisterNode / Heartbeat','storage',p)
        d.group(p+'rep',x+35,870,410,225,'Replica · shard 0','raft',p,True)
        d.node(p+'core',x+55,930,370,70,'RaftCore + 状态机',('Leader' if i==0 else 'Follower')+' · 独立日志与状态','raft',p+'rep')
        d.node(p+'map',x+55,1030,170,55,'内存 Map','','storage',p+'rep')
        d.node(p+'disk',x+255,1030,170,55,'WAL / Snapshot','','persist',p+'rep')
        d.edge(p+'core',p+'map',[(x+140,1000),(x+140,1030)],'apply',(x+140,1015))
        d.edge(p+'core',p+'disk',[(x+340,1000),(x+340,1030)],'磁盘',(x+340,1015),kind='disk')
        sx=1170+i*160;ay=420+i*60
        d.edge('topoapi',p+'agent',[(sx,310),(sx,ay),(x+240,ay),(x+240,710)],'gRPC：注册 / 心跳上报\n响应返回 ExpectedReplica',(x+240,560),'rpc',True)
    d.edge('sdk','s0core',[(320,310),(320,610),(20,610),(20,965),(95,965)],'gRPC：Put / Get / Delete',(170,610),'rpc')
    d.edge('s0core','s1core',[(465,965),(665,965)],'Raft gRPC',(565,920),'rpc',True)
    d.edge('s0core','s2core',[(465,985),(565,985),(565,1120),(1115,1120),(1115,985),(1235,985)],'Leader ↔ Follower C：Raft gRPC',(850,1120),'rpc',True)
    return d


def sdk():
    d=Diagram('02-sdk-sharding','02｜SDK、路由缓存与分片','应用内的 SDK 不在每次 KV 请求中调用 Catalog；每个 key 用稳定哈希定位固定 shard。',1400,960)
    d.group('sdk',40,135,865,700,'应用进程中的 SDK','sdk')
    d.node('kv',75,205,255,115,'KVClient','总 deadline / 重试策略','sdk','sdk')
    d.node('cache',455,205,400,115,'RouteCache','resolve_route / refresh','sdk','sdk')
    d.node('hash',85,430,280,130,'stable_shard_index','FNV-1a(key) % shard_count','app','sdk')
    d.node('snapshot',465,430,390,130,'TableRouteSnapshot','table_id / shard_count / routes\natomic_load / atomic_store','sdk','sdk')
    d.node('storageclient',85,675,280,100,'StorageClient','选 Leader；检查两层状态','sdk','sdk')
    d.node('topoclient',465,675,390,100,'TopoRouteClient','获取整表路由','sdk','sdk')
    d.node('topo',1070,205,285,115,'TopoService','GetTableRoutes','topo')
    d.node('storage',1070,675,285,100,'StorageService','Put / Get / Delete','storage')
    d.edge('kv','cache',[(330,260),(455,260)],'调用：解析 / 刷新',(390,225))
    d.edge('cache','hash',[(495,320),(495,380),(225,380),(225,430)],'调用：计算 shard_index',(295,380))
    d.edge('cache','snapshot',[(690,320),(690,430)],'调用：读取 / 发布',(690,375))
    d.edge('cache','topoclient',[(855,260),(885,260),(885,725),(855,725)],'调用：refresh\n后台或按需',(825,610))
    d.edge('topoclient','topo',[(855,750),(985,750),(985,260),(1070,260)],'gRPC：GetTableRoutes',(990,590),'rpc')
    d.edge('kv','storageclient',[(75,275),(55,275),(55,725),(85,725)],'调用：send(route, timeout)',(225,620))
    d.edge('storageclient','storage',[(225,775),(225,815),(1020,815),(1020,725),(1070,725)],'gRPC：KV 请求 + replica_id',(730,815),'rpc')
    return d


def control():
    d=Diagram('03-control-plane','03｜Catalog、Topo 与副本控制','DDL 接纳与表就绪分开；Topo 的副本指令随 Heartbeat 响应返回，NodeAgent 在本进程执行。',1800,1420)
    d.group('cat',40,145,700,790,'Catalog 进程','catalog')
    for args in [('ch',70,215,255,105,'CatalogServiceImpl','RPC 参数与状态转换'),('ddl',410,215,290,105,'DdlService','建表 / 删表 / 改副本'),('store',70,470,290,105,'CatalogStore','DB / Table / operation_id'),('recon',410,470,290,105,'TableReconciler','查询、重提、完成状态'),('persist',70,760,290,105,'CatalogPersistEngine','持久化库表状态'),('tc',410,760,290,105,'TopoClient','Place / Alter / Drop / Status')]:
        d.node(*args,'catalog','cat')
    d.edge('ch','ddl',[(325,267),(410,267)],'调用',(370,240))
    d.edge('ddl','store',[(555,320),(555,390),(215,390),(215,470)],'调用：先保存 DDL 状态',(350,390))
    d.edge('recon','store',[(410,522),(360,522)],'调用',(385,550))
    d.edge('store','persist',[(215,575),(215,760)],'调用：持久化',(215,680))
    d.edge('recon','tc',[(555,575),(555,760)],'调用：检查 / 重试',(555,680))
    d.edge('ddl','tc',[(700,267),(720,267),(720,812),(700,812)],'调用：提交目标',(720,620))
    d.node('catfile',70,1010,290,100,'Catalog 本地文件','库表元数据','persist')
    d.edge('persist','catfile',[(215,865),(215,1010)],'磁盘：保存 / 恢复',(215,970),'disk')
    d.group('top',820,145,930,790,'Topo 进程','topo')
    d.node('th',850,215,335,105,'TopoServiceImpl','gRPC 入口','topo','top')
    d.node('mgr',1340,215,375,105,'ServiceManager','分发 RPC 与后台任务','topo','top')
    d.node('table',850,425,335,90,'TableService','目标规格 / 就绪判定','topo','top')
    d.node('node',1340,425,375,90,'NodeService','注册 / 心跳 / 健康状态','topo','top')
    d.node('route',850,630,335,90,'RouteService','发布唯一可写 Leader 路由','topo','top')
    d.node('group',1340,630,375,90,'ReplicaGroupService','构建心跳 expects / 收敛','topo','top')
    d.node('ts',850,810,335,85,'TopoStore','表 / 节点 / 副本 / 路由','topo','top')
    d.node('plan',1340,810,375,85,'Plan / Membership Reconciler','规划目标 / 调整成员','topo','top')
    d.edge('tc','th',[(700,840),(780,840),(780,110),(1015,110),(1015,215)],'gRPC：Place / Alter / Drop / GetTableStatus',(900,110),'rpc')
    d.edge('th','mgr',[(1185,267),(1340,267)],'调用：dispatch',(1260,235))
    d.edge('mgr','table',[(1385,320),(1385,370),(1015,370),(1015,425)],'调用：DDL / 状态',(1160,370))
    d.edge('mgr','node',[(1580,320),(1580,425)],'调用：Heartbeat',(1580,370))
    d.edge('mgr','route',[(1340,290),(1270,290),(1270,575),(1015,575),(1015,630)],'调用：查询 / 更新路由',(1110,575))
    d.edge('mgr','group',[(1715,285),(1730,285),(1730,675),(1715,675)],'调用：build_heartbeat_result',(1515,575))
    d.edge('table','ts',[(850,470),(835,470),(835,852),(850,852)],'调用：read / write',(895,590))
    d.edge('route','ts',[(1015,720),(1015,810)],'调用：读写路由',(1015,765))
    d.edge('node','ts',[(1340,470),(1290,470),(1290,740),(1150,740),(1150,810)],'调用：更新观测状态',(1290,550))
    d.edge('group','plan',[(1525,720),(1525,810)],'调用：reconcile',(1525,765))
    d.edge('plan','ts',[(1340,852),(1185,852)],'调用：read / write',(1260,910))
    d.node('topfile',500,1010,300,100,'Topo 本地元数据','PersistentMetaStore','persist')
    d.edge('ts','topfile',[(900,895),(900,990),(650,990),(650,1010)],'磁盘：保存 / 恢复',(700,990),'disk')
    d.group('storage',910,1040,840,255,'Storage 进程','storage')
    d.node('agent',940,1130,330,105,'NodeAgent','注册 / 心跳；执行 expects','storage','storage')
    d.node('rm',1420,1130,300,105,'ReplicaManager','创建 / 删除 / 成员调用','storage','storage')
    d.edge('agent','th',[(1105,1130),(1105,1000),(1770,1000),(1770,340),(1235,340),(1235,245),(1185,245)],'gRPC：RegisterNode / Heartbeat\n响应携带 ExpectedReplica',(1515,990),'rpc',True)
    d.edge('agent','rm',[(1270,1182),(1420,1182)],'本地回调：replica_ops',(1345,1250))
    return d


def storage():
    d=Diagram('04-storage','04｜Storage 进程与多个 Replica','ReplicaManager 按 replica_id 找到对象；一个节点可管理多个 shard，每个 Replica 有独立 Raft 和持久化状态。',1620,1200)
    d.node('sdk',40,135,310,100,'SDK / 其他 Storage','KV RPC / Raft RPC','sdk')
    d.node('topo',1210,135,360,100,'TopoService','Heartbeat / ExpectedReplica','topo')
    d.group('process',40,325,1530,750,'Storage 进程','storage')
    d.node('handler',85,405,410,110,'StorageServiceImpl','Put / Get / Delete / Raft RPC','storage','process')
    d.node('manager',85,645,410,110,'ReplicaManager','replica_map / shard_primary_index','storage','process')
    d.node('agent',1150,405,360,110,'NodeAgent','执行副本和成员指令','storage','process')
    d.group('r0',610,575,440,430,'Replica · shard 0','raft','process',True)
    d.group('r1',1100,575,410,430,'Replica · shard 1','raft','process',True)
    for p,x,w in [('r0',640,380),('r1',1130,350)]:
        d.node(p+'loop',x,650,w,100,'ReplicaLoop + RaftCore','每个 Replica 的协议状态','raft',p)
        d.node(p+'state',x,815,w,130,'状态机 + PersistEngine','内存 Map / request record\n本副本 WAL / Snapshot / meta','persist',p)
        d.edge(p+'loop',p+'state',[(x+w/2,750),(x+w/2,815)],'Replica 内部协作',(x+w/2,785))
    d.edge('sdk','handler',[(195,235),(195,405)],'gRPC：StorageService',(195,280),'rpc')
    d.edge('topo','agent',[(1390,235),(1390,405)],'gRPC：注册 / 心跳\n响应：expects',(1390,280),'rpc',True)
    d.edge('handler','manager',[(290,515),(290,645)],'调用：get_replica_by_id',(290,580))
    d.edge('manager','r0loop',[(495,695),(640,695)],'调用目标 Replica',(565,665))
    d.edge('manager','r1loop',[(370,755),(370,1035),(1070,1035),(1070,700),(1130,700)],'按 ID 定位其他 shard Replica',(710,1035))
    d.edge('agent','manager',[(1150,450),(550,450),(550,605),(400,605),(400,645)],'本地回调：create / delete / add_member / remove_member',(780,450))
    return d


def communication():
    d=Diagram('05-replica-raft-communication','05｜Replica 与 RaftCore 的通信闭环','普通 Raft 消息经工作池异步发送；Get 的 ReadIndex 使用同步确认路径。Put OK 以提案提交为条件。',1840,1410)
    d.node('remote',1420,130,370,100,'其他 Storage 进程','StorageService → Replica','storage')
    d.group('replica',40,290,1750,990,'当前 Replica 对象','raft',object=True)
    d.node('facade',75,365,350,110,'Replica','put / Raft handler / tick','storage','replica')
    d.node('loop',565,365,445,110,'ReplicaLoop','BatchDispatchQueue → SerialTaskRunner','raft','replica')
    d.node('core',1165,365,560,110,'RaftCore','propose / tick / handle_*；产出 Effects','raft','replica')
    d.node('effects',1165,610,560,115,'RaftEffects','hard_state / WAL entries / messages','raft','replica')
    d.node('persist',585,610,395,115,'PersistEngine','save_raft_meta / append_wal / rewrite','persist','replica')
    d.node('dispatcher',585,865,395,115,'ReplicaMessageDispatcher','RPC 工作池；async_send(messages)','raft','replica')
    d.node('sender',1155,865,285,115,'RaftSender','构造 / 发送协议 RPC','raft','replica')
    d.node('transport',1495,865,255,115,'GrpcRaftRpcTransport','gRPC Stub / Channel','storage','replica')
    d.node('read',75,865,390,115,'ReplicaReadIndexChecker','BuildReadIndexCall；同步确认多数派','storage','replica')
    d.node('applier',75,1130,390,100,'ReplicaApplier','读已提交日志 → 状态机 apply','storage','replica')
    d.node('state',585,1130,395,100,'KvStateMachine','Map + request record','storage','replica')
    d.node('task',1165,1130,540,100,'ReplicaApplyTask','后台周期任务 / notify_apply_task','storage','replica')
    d.edge('facade','loop',[(425,420),(565,420)],'队列：Call / TickEvent',(495,350),'event')
    d.edge('loop','core',[(1010,420),(1165,420)],'调用：run_step(step)',(1085,385))
    d.edge('core','effects',[(1445,475),(1445,610)],'返回：状态变化 / Effects',(1445,555))
    d.edge('effects','persist',[(1165,650),(980,650)],'① 调用：先持久化',(1080,615))
    d.edge('effects','dispatcher',[(1280,725),(1280,790),(780,790),(780,865)],'② 持久化成功后调用：async_send',(1000,790))
    d.edge('dispatcher','sender',[(980,895),(1155,895)],'工作池调用',(1060,825),'event')
    d.edge('dispatcher','sender',[(980,955),(1155,955)],'读确认：同步调用',(1060,1005))
    d.edge('sender','transport',[(1440,920),(1495,920)],'调用',(1468,850))
    d.edge('transport','remote',[(1710,865),(1810,865),(1810,180),(1790,180)],'gRPC：PreVote / RequestVote\nAppendEntries / InstallSnapshot',(1620,265),'rpc',True)
    d.edge('dispatcher','loop',[(650,865),(650,770),(540,770),(540,455),(565,455)],'异步回调：ResponseEvent / SendFailedEvent\nasync_submit → handle_event',(335,740),'event')
    d.edge('facade','read',[(190,475),(190,865)],'Get：调用读检查',(210,560))
    d.edge('read','loop',[(465,910),(515,910),(515,390),(565,390)],'队列调用：BuildReadIndexCall\n同步等待；响应再提交 Loop',(515,550),'event')
    d.edge('read','dispatcher',[(465,945),(585,945)],'同步发送',(525,1005))
    d.edge('read','facade',[(390,865),(390,475)],'返回：read_index',(390,815))
    d.edge('facade','applier',[(75,445),(55,445),(55,1090),(170,1090),(170,1130)],'Get 确认后调用 Applier',(215,1050))
    d.edge('task','applier',[(1165,1170),(1040,1170),(1040,1075),(330,1075),(330,1130)],'后台调用：Replica → Applier',(760,1075))
    d.edge('applier','core',[(75,1180),(55,1180),(55,1250),(1770,1250),(1770,440),(1725,440)],'调用：extract_committed_entries / advance_last_applied',(1310,1250))
    d.edge('applier','state',[(465,1180),(585,1180)],'调用：apply',(525,1140))
    return d


def raft():
    d=Diagram('06-raft-core','06｜RaftCore 内部组件与状态机边界','Core 在外部 raft_core_mutex 保护下计算协议状态；持久化、网络发送与业务 Map 位于 Core 外部。',1620,1270)
    d.node('loop',40,135,440,100,'ReplicaLoop / ReplicaApplier','调用 Core；消费 Effects / 已提交日志','storage')
    d.group('core',40,360,1530,770,'RaftCore 对象','raft',object=True)
    d.node('entry',620,425,390,90,'RaftCore 方法','协调组件；计算协议变化与 Effects','raft','core')
    d.node('election',85,625,405,115,'RaftElection','role / term / voted_for\nPreVote / 正式选举','raft','core')
    d.node('membership',85,920,405,115,'RaftMembership','Voter / Learner / quorum','raft','core')
    d.node('log',620,625,390,115,'RaftLog','日志 index / term\nSnapshot 边界与前缀匹配','raft','core')
    d.node('apply',1160,625,370,115,'RaftApply','commit_index / last_applied\n提取已提交日志','raft','core')
    d.group('repgroup',620,880,910,220,'复制职责（含 PeerProgress）','raft','core',True)
    d.node('repl',655,950,395,100,'RaftReplication','广播消息 / 多数派提交判定','raft','repgroup')
    d.node('progress',1195,950,300,100,'RaftPeerProgress','next / match index\nSnapshot 水位','raft','repgroup')
    d.node('sm',1160,135,370,100,'KvStateMachine / Map','Core 外的业务状态','storage')
    d.edge('loop','entry',[(245,235),(245,300),(815,300),(815,425)],'调用：Core 入口',(780,300))
    d.edge('entry','election',[(620,470),(550,470),(550,680),(490,680)],'调用：选举状态',(400,560))
    d.edge('entry','log',[(815,515),(815,625)],'调用：日志检查 / 修改',(815,570))
    d.edge('entry','membership',[(620,495),(525,495),(525,975),(490,975)],'调用：资格 / quorum',(315,850))
    d.edge('entry','repl',[(1010,470),(1080,470),(1080,935),(850,935),(850,950)],'调用：复制 / 提交判定',(1145,855))
    d.edge('entry','apply',[(1010,490),(1345,490),(1345,625)],'调用：提交 / 读条件',(1270,540))
    d.edge('repl','membership',[(655,1000),(490,1000)],'调用：Voter / quorum',(565,1080))
    d.edge('repl','log',[(655,980),(595,980),(595,710),(620,710)],'调用：构造日志消息',(660,805))
    d.edge('repl','progress',[(1050,1000),(1195,1000)],'调用：复制进度',(1120,1070))
    d.edge('repl','apply',[(1050,980),(1115,980),(1115,685),(1160,685)],'调用：推进 commit_index',(1280,810))
    d.edge('apply','log',[(1160,660),(1010,660)],'调用：提交前缀',(1085,605))
    d.edge('loop','sm',[(480,185),(1160,185)],'Applier 调用：已提交日志 → apply',(810,160))
    return d


def persistence():
    d=Diagram('07-persistence-recovery','07｜持久化、Snapshot 与恢复','Snapshot 对应明确 apply 边界；恢复先还原快照与 Raft 日志，后续已提交日志由 Applier 推进。',1640,1350)
    d.group('rep',40,140,1110,1050,'Replica 对象','storage',object=True)
    d.node('core',80,220,360,115,'RaftCore / ReplicaLoop','meta / WAL Effects\n加载 Raft 状态与日志','raft','rep')
    d.node('applier',690,220,405,115,'ReplicaApplier','extract committed → apply','storage','rep')
    d.node('state',690,505,405,115,'KvStateMachine','request record / apply index / term','storage','rep')
    d.node('map',690,760,405,100,'MapEngine','运行时内存 KV','storage','rep')
    d.node('snap',80,505,360,115,'ReplicaSnapshotCoordinator','捕获 / 安装 / 发布快照边界','storage','rep')
    d.node('persist',80,760,360,100,'PersistEngine','文件编码、校验、可靠写入','persist','rep')
    d.node('recover',80,1010,1015,110,'Replica::recover','还原 Snapshot 到状态机；meta / WAL 加载到 RaftCore\n损坏或缺口 → RECOVERING；后续通过日志 / Snapshot 补齐','storage','rep')
    d.group('disk',1240,140,350,1050,'本副本本地磁盘','persist')
    d.node('meta',1270,220,290,115,'Raft meta','term / voted_for','persist','disk')
    d.node('wal',1270,505,290,115,'WAL','日志记录 / index / CRC','persist','disk')
    d.node('snapshot',1270,760,290,135,'Snapshot','KV / request record\napply index、term / members','persist','disk')
    d.edge('applier','core',[(690,270),(440,270)],'调用：提取 / 推进 apply 位置',(565,235))
    d.edge('applier','state',[(892,335),(892,505)],'调用：apply(entry)',(892,410))
    d.edge('state','map',[(892,620),(892,760)],'调用：读 / 写 KV',(892,685))
    d.edge('snap','state',[(440,565),(690,565)],'调用：capture / restore',(565,530))
    d.edge('snap','persist',[(260,620),(260,760)],'调用：write / receive Snapshot',(290,685))
    d.edge('core','persist',[(80,280),(60,280),(60,810),(80,810)],'调用：persist_raft_effects',(270,425))
    d.edge('persist','meta',[(370,760),(370,700),(1175,700),(1175,275),(1270,275)],'磁盘：save / load meta',(1210,370),'disk')
    d.edge('persist','wal',[(440,790),(510,790),(510,655),(1205,655),(1205,565),(1270,565)],'磁盘：append / rewrite / read WAL',(1060,655),'disk')
    d.edge('persist','snapshot',[(440,840),(540,840),(540,900),(1180,900),(1180,827),(1270,827)],'磁盘：Snapshot 先可靠发布，再裁剪 WAL',(815,900),'disk')
    d.edge('recover','persist',[(260,1010),(260,860)],'调用：recover',(260,940))
    d.edge('recover','core',[(80,1060),(50,1060),(50,250),(80,250)],'调用：恢复 Core',(265,980))
    d.edge('recover','state',[(1095,1060),(1125,1060),(1125,590),(1095,590)],'调用：restore Snapshot',(920,980))
    return d


if __name__ == '__main__':
    for factory in (cluster,sdk,control,storage,communication,raft,persistence):
        d=factory();d.render();print(d.name)
