"""Translation for text not related to cogs."""

from babel.support import LazyProxy

from ..i18n import Translator

translator = Translator(__name__)


def _callback(message, *args, **kwargs):
    return translator(message, *args, **kwargs)


def _(message, *args, **kwargs):
    return LazyProxy(_callback, message, *args, **kwargs, enable_cache=False)


PERMISSIONS = {
    'create_instant_invite': _('Criar convite'),
    'kick_members': _('Expulsar membros'),
    'ban_members': _('Banir membros'),
    'administrator': _('Administrador'),
    'manage_channels': _('Gerenciar canais'),
    'manage_guild': _('Gerenciar servidor'),
    'add_reactions': _('Adicionar reações'),
    'view_audit_log': _('Ver o registro de auditoria'),
    'priority_speaker': _('Voz Prioritária'),
    'stream': _('Vídeo'),
    'read_messages': _('Ver canal'),
    'send_messages': _('Enviar mensagens'),
    'send_tts_messages': _('Enviar mensagens em TTS'),
    'manage_messages': _('Gerenciar mensagens'),
    'embed_links': _('Inserir links'),
    'attach_files': _('Anexar arquivos'),
    'read_message_history': _('Ver histórico de mensagens'),
    'mention_everyone': _('Mencionar todos'),
    'external_emojis': _('Usar emojis externos'),
    'view_guild_insights': _('Ver Análises do Servidor'),
    'connect': _('Conectar'),
    'speak': _('Falar'),
    'mute_members': _('Silenciar membros'),
    'deafen_members': _('Ensurdecer membros'),
    'move_members': _('Mover membros'),
    'use_voice_activation': _('Usar detecção de voz'),
    'change_nickname': _('Alterar apelido'),
    'manage_nicknames': _('Gerenciar apelidos'),
    'manage_roles': _('Gerenciar cargos'),
    'manage_webhooks': _('Gerenciar webhooks'),
    'manage_emojis': _('Gerenciar emojis'),
    'use_slash_commands': _('Usar comandos /'),
    'request_to_speak': _('Pedir para falar'),
    # TODO: Use the name client uses.
    'manage_events': _('Gerenciar eventos do servidor'),
    'manage_threads': _('Gerenciar Threads'),
    'use_threads': _('Utilizar Threads Públicas'),
    'use_private_threads': _('Utilizar Threads Privadas'),
}

CONFIRM = {'yes': _('Sim'), 'no': _('Não')}

ERRORS = {
    'not_in_range': _('Insira um número entre {0.min} e {0.max}.'),
    'reserved_prefix': _('Esse prefixo está reservado.'),
}
