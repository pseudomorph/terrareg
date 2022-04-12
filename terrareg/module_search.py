
import datetime

import sqlalchemy
from terrareg.config import TRUSTED_NAMESPACES

from terrareg.database import Database
import terrareg.models
from terrareg.filters import NamespaceTrustFilter


class ModuleSearch(object):

    @staticmethod
    def search_module_providers(
        offset: int,
        limit: int,
        query: str=None,
        namespace: str=None,
        provider: str=None,
        verified: bool=False,
        namespace_trust_filters: list=NamespaceTrustFilter.UNSPECIFIED):

        db = Database.get()
        select = db.module_version.select()

        if query:
            for query_part in query.split():
                wildcarded_query_part = '%{0}%'.format(query_part)
                select = select.where(
                    sqlalchemy.or_(
                        db.module_version.c.namespace.like(query_part),
                        db.module_version.c.module.like(wildcarded_query_part),
                        db.module_version.c.provider.like(query_part),
                        db.module_version.c.version.like(query_part),
                        db.module_version.c.description.like(wildcarded_query_part),
                        db.module_version.c.owner.like(wildcarded_query_part)
                    )
                )

        # If provider has been supplied, select by that
        if provider:
            select = select.where(
                db.module_version.c.provider == provider
            )

        # If namespace has been supplied, select by that
        if namespace:
            select = select.where(
                db.module_version.c.namespace == namespace
            )

        # Filter by verified modules, if requested
        if verified:
            select = select.where(
                db.module_version.c.verified == True
            )

        if namespace_trust_filters is not NamespaceTrustFilter.UNSPECIFIED:
            or_query = []
            if NamespaceTrustFilter.TRUSTED_NAMESPACES in namespace_trust_filters:
                or_query.append(db.module_version.c.namespace.in_(tuple(TRUSTED_NAMESPACES)))
            if NamespaceTrustFilter.CONTRIBUTED in namespace_trust_filters:
                or_query.append(~db.module_version.c.namespace.in_(tuple(TRUSTED_NAMESPACES)))
            select = select.where(sqlalchemy.or_(*or_query))


        # Group by and order by namespace, module and provider
        select = select.group_by(
            db.module_version.c.namespace,
            db.module_version.c.module,
            db.module_version.c.provider
        ).order_by(
            db.module_version.c.namespace.asc(),
            db.module_version.c.module.asc(),
            db.module_version.c.provider.asc()
        ).limit(limit).offset(offset)

        conn = db.get_engine().connect()
        res = conn.execute(select)

        module_providers = []
        for r in res:
            namespace = terrareg.models.Namespace(name=r['namespace'])
            module = terrareg.models.Module(namespace=namespace, name=r['module'])
            module_providers.append(terrareg.models.ModuleProvider(module=module, name=r['provider']))

        return module_providers

    @staticmethod
    def get_most_recently_published():
        """Return module with most recent published date."""
        db = Database.get()
        select = db.module_version.select().where(
        ).order_by(db.module_version.c.published_at.desc(), 
        ).limit(1)

        conn = db.get_engine().connect()
        res = conn.execute(select)

        row = res.fetchone()
        namespace = terrareg.models.Namespace(name=row['namespace'])
        module = terrareg.models.Module(namespace=namespace,
                                        name=row['module'])
        module_provider = terrareg.models.ModuleProvider(module=module,
                                                         name=row['provider'])
        return terrareg.models.ModuleVersion(module_provider=module_provider,
                                             version=row['version'])

    @staticmethod
    def get_most_downloaded_module_provider_this_Week():
        """Obtain module provider with most downloads this week."""
        db = Database.get()
        conn = db.get_engine().connect()
        counts = sqlalchemy.select(
            [
                sqlalchemy.func.count().label('download_count'),
                db.module_version.c.namespace,
                db.module_version.c.module,
                db.module_version.c.provider
            ]
        ).select_from(
            db.analytics
        ).join(
            db.module_version,
            db.module_version.c.id == db.analytics.c.parent_module_version
        ).where(
            db.analytics.c.timestamp >= (
                datetime.datetime.now() -
                datetime.timedelta(days=7)
            )
        ).group_by(
            db.module_version.c.namespace,
            db.module_version.c.module,
            db.module_version.c.provider
        ).subquery()

        select = counts.select(
        ).order_by(counts.c.download_count.desc()
        ).limit(1)

        conn = db.get_engine().connect()
        res = conn.execute(select)

        row = res.fetchone()
        namespace = terrareg.models.Namespace(name=row['namespace'])
        module = terrareg.models.Module(namespace=namespace,
                                        name=row['module'])
        return terrareg.models.ModuleProvider(module=module,
                                              name=row['provider'])
