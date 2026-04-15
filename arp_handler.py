from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.packet.ethernet import ethernet, ETHER_BROADCAST
from pox.lib.packet.arp import arp

log = core.getLogger()
arp_table = {}

def _handle_ConnectionUp(event):
    log.info("Switch connected")

def _handle_PacketIn(event):
    packet = event.parsed

    if not packet.parsed:
        return

    if packet.type == ethernet.ARP_TYPE:
        a = packet.payload

        # Learn sender IP -> MAC
        arp_table[a.protosrc] = a.hwsrc
        log.info("Learned %s -> %s", a.protosrc, a.hwsrc)

        # ARP Request
        if a.opcode == arp.REQUEST:
            if a.protodst in arp_table:
                reply = arp()
                reply.opcode = arp.REPLY
                reply.hwsrc = arp_table[a.protodst]
                reply.hwdst = a.hwsrc
                reply.protosrc = a.protodst
                reply.protodst = a.protosrc

                eth = ethernet(type=ethernet.ARP_TYPE,
                               src=reply.hwsrc,
                               dst=reply.hwdst)
                eth.payload = reply

                msg = of.ofp_packet_out()
                msg.data = eth.pack()
                msg.actions.append(of.ofp_action_output(port=event.port))
                event.connection.send(msg)

                log.info("Sent ARP reply for %s", a.protodst)

def launch():
    core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
    core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
    log.info("ARP Handler Loaded")
