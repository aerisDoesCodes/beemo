from discord.ext import commands

import discord

class PermissionError(commands.CommandError):
    pass

def is_owner_check(ctx):
    return ctx.message.author.id in ctx.bot.owners

def is_owner():
    return commands.check(is_owner_check)


def check_permissions(ctx, perms):
    msg = ctx.message
    try:
        if is_owner_check(ctx):
            return True
    except PermissionError:
        pass

    ch = msg.channel
    author = msg.author
    resolved = ch.permissions_for(author)
    return all(getattr(resolved, name, None) == value for name, value in perms.items())

def role_or_permissions(ctx, check, **perms):
    if check_permissions(ctx, perms):
        return True

    ch = ctx.message.channel
    author = ctx.message.author
    if ch.is_private:
        return False # can't have roles in PMs

    role = discord.utils.find(check, author.roles)
    return role is not None

def role_and_permissions(ctx, check, **perms):
    ch = ctx.message.channel
    author = ctx.message.author
    if ch.is_private:
        return False # can't have roles in PMs

    role = discord.utils.find(check, author.roles)
    return role is not None and check_permissions(ctx, perms)

def music_or_permissions(**perms):
    def predicate(ctx):
        def role_check(r):
            if r.name in ('Beemo Music', 'Beemo Admin'):
                return True
            return False
        result = role_or_permissions(ctx, role_check, **perms)
        if result is False:
            raise PermissionError("You need the `Beemo Music` role to do this (or permission `{0}`)".format("`, `".join(perms).replace("_", " ")))
        return True

    return commands.check(predicate)

def admin_or_permissions(**perms):
    def predicate(ctx):
        def role_check(r):
            if r.name == 'Beemo Admin':
                return True
            return False
        result = role_or_permissions(ctx, role_check, **perms)
        if result is False:
            raise PermissionError("You need the `Beemo Admin` role to do this (or permission `{0}`)".format("`, `".join(perms).replace("_", " ")))
        return True

    return commands.check(predicate)

def admin_and_permissions(**perms):
    def predicate(ctx):
        def role_check(r):
            try:
                if is_owner_check(ctx):
                    return True
            except PermissionError:
                pass
            if r.name == 'Beemo Admin':
                return True
            return False
        result = role_and_permissions(ctx, role_check, **perms)
        if result is False:
            raise PermissionError("You need the `Beemo Admin` role to do this (and permission(s) `{0}`)".format("`, `".join(perms).replace("_", " ")))
        return True

    return commands.check(predicate)

def is_in_servers(*server_ids):
    def predicate(ctx):
        server = ctx.message.server
        if server is None:
            return False
        return server.id in server_ids
    return commands.check(predicate)