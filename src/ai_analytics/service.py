"""AI Analytics service."""

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai_core.service import AIService

from .models import AIAnalyticsQuery

logger = logging.getLogger(__name__)


class AIAnalyticsService:
    """Service for AI-powered analytics."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIService()

    async def process_analytics_query(
        self,
        natural_query: str,
        organization_id: int,
        user_id: int,
        chart_type: Optional[str] = None,
    ) -> AIAnalyticsQuery:
        """Process a natural language analytics query."""
        try:
            # Create query record
            query_record = AIAnalyticsQuery(
                organization_id=organization_id,
                user_id=user_id,
                natural_query=natural_query,
                status='pending',
            )

            self.db.add(query_record)
            await self.db.commit()
            await self.db.refresh(query_record)

            # Convert natural language to SQL
            sql_query = await self._convert_to_sql(natural_query, organization_id, user_id)

            if not sql_query:
                query_record.status = 'failed'
                query_record.error_message = "Could not convert query to SQL"
                await self.db.commit()
                return query_record

            # Execute SQL query
            results = await self._execute_sql_query(sql_query)

            # Generate chart configuration
            chart_config = await self._generate_chart_config(
                results, chart_type, natural_query, organization_id, user_id
            )

            # Generate insights
            insights = await self._generate_insights(
                results, natural_query, organization_id, user_id
            )

            # Update query record
            query_record.sql_query = sql_query
            query_record.results = results
            query_record.chart_config = chart_config
            query_record.status = 'completed'

            # Estimate tokens and cost (rough)
            tokens_used = self.ai_service.provider.count_tokens(natural_query + str(results))
            cost = self.ai_service.provider.estimate_cost(tokens_used, 0)

            query_record.tokens_used = tokens_used
            query_record.cost = cost

            await self.db.commit()
            await self.db.refresh(query_record)

            return query_record

        except Exception as e:
            logger.error(f"Analytics query processing failed: {str(e)}")
            # Update status to failed
            if 'query_record' in locals():
                query_record.status = 'failed'
                query_record.error_message = str(e)
                await self.db.commit()
            raise

    async def _convert_to_sql(
        self, natural_query: str, organization_id: int, user_id: int
    ) -> Optional[str]:
        """Convert natural language to SQL using AI."""
        try:
            # Get database schema information
            schema_info = await self._get_database_schema()

            prompt = f"""Convert the following natural language query to SQL. 
            Use only the tables and columns provided in the schema.

            Database Schema:
            {schema_info}

            Natural Language Query: {natural_query}

            Requirements:
            - Use only SELECT statements
            - Include proper WHERE clauses for organization_id = {organization_id}
            - Return only the SQL query, no explanations
            - Use proper SQL syntax for PostgreSQL
            - Limit results to 1000 rows maximum

            SQL Query:"""

            sql_query = await self.ai_service.generate_text(
                prompt=prompt,
                temperature=0.1,  # Low temperature for more consistent SQL
                organization_id=organization_id,
                user_id=user_id,
                feature="sql_generation",
            )

            # Clean up the response
            sql_query = sql_query.strip()
            if sql_query.startswith('```sql'):
                sql_query = sql_query[6:]
            if sql_query.endswith('```'):
                sql_query = sql_query[:-3]
            sql_query = sql_query.strip()

            # Basic validation
            if not sql_query.upper().startswith('SELECT'):
                return None

            return sql_query

        except Exception as e:
            logger.error(f"SQL conversion failed: {str(e)}")
            return None

    async def _get_database_schema(self) -> str:
        """Get database schema information."""
        # This is a simplified schema - in production, you'd query the actual schema
        schema_info = """
        Tables:
        - users (id, email, created_at, organization_id)
        - organizations (id, name, created_at)
        - projects (id, name, description, organization_id, created_at)
        - ai_usage_logs (id, organization_id, feature, tokens_used, cost, created_at)
        - ai_content_generations (id, user_id, content_type, tokens_used, cost, created_at)
        - ai_documents (id, organization_id, name, status, created_at)
        """
        return schema_info

    async def _execute_sql_query(self, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query safely."""
        try:
            # Basic safety checks
            dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
            if any(keyword in sql_query.upper() for keyword in dangerous_keywords):
                raise ValueError("Query contains dangerous operations")

            # Execute query
            result = await self.db.execute(text(sql_query))
            rows = result.fetchall()
            columns = result.keys()

            # Convert to dictionary format
            data = []
            for row in rows:
                row_dict = {}
                for i, column in enumerate(columns):
                    value = row[i]
                    # Convert datetime objects to strings
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    row_dict[column] = value
                data.append(row_dict)

            return {
                "data": data,
                "columns": list(columns),
                "row_count": len(data),
            }

        except Exception as e:
            logger.error(f"SQL execution failed: {str(e)}")
            raise ValueError(f"Query execution failed: {str(e)}")

    async def _generate_chart_config(
        self,
        results: Dict[str, Any],
        chart_type: Optional[str],
        natural_query: str,
        organization_id: int,
        user_id: int,
    ) -> Dict[str, Any]:
        """Generate chart configuration using AI."""
        try:
            if not results.get("data"):
                return {"type": "table", "data": [], "title": "No Data"}

            # Determine chart type if not provided
            if not chart_type:
                chart_type = await self._suggest_chart_type(results, natural_query, organization_id, user_id)

            # Generate chart configuration
            prompt = f"""Based on the query results, create a chart configuration.

            Query: {natural_query}
            Chart Type: {chart_type}
            Data: {json.dumps(results['data'][:10], default=str)}  # First 10 rows

            Create a JSON configuration with:
            - type: chart type
            - title: descriptive title
            - x_axis: column name for x-axis
            - y_axis: column name for y-axis
            - data: formatted data array
            - options: chart-specific options

            Return only valid JSON:"""

            config_json = await self.ai_service.generate_text(
                prompt=prompt,
                temperature=0.3,
                organization_id=organization_id,
                user_id=user_id,
                feature="chart_config_generation",
            )

            # Parse JSON response
            try:
                config = json.loads(config_json.strip())
                return config
            except json.JSONDecodeError:
                # Fallback configuration
                return self._create_fallback_chart_config(results, chart_type)

        except Exception as e:
            logger.error(f"Chart config generation failed: {str(e)}")
            return self._create_fallback_chart_config(results, chart_type or "table")

    async def _suggest_chart_type(
        self, results: Dict[str, Any], natural_query: str, organization_id: int, user_id: int
    ) -> str:
        """Suggest appropriate chart type."""
        try:
            prompt = f"""Based on the query and data, suggest the best chart type.

            Query: {natural_query}
            Data columns: {results.get('columns', [])}
            Sample data: {json.dumps(results['data'][:3], default=str)}

            Choose from: bar, line, pie, table, area, scatter

            Return only the chart type name:"""

            chart_type = await self.ai_service.generate_text(
                prompt=prompt,
                temperature=0.1,
                organization_id=organization_id,
                user_id=user_id,
                feature="chart_type_suggestion",
            )

            chart_type = chart_type.strip().lower()
            valid_types = ['bar', 'line', 'pie', 'table', 'area', 'scatter']

            if chart_type in valid_types:
                return chart_type
            else:
                return 'table'  # Default fallback

        except Exception as e:
            logger.error(f"Chart type suggestion failed: {str(e)}")
            return 'table'

    def _create_fallback_chart_config(self, results: Dict[str, Any], chart_type: str) -> Dict[str, Any]:
        """Create fallback chart configuration."""
        data = results.get("data", [])
        columns = results.get("columns", [])

        if not data or not columns:
            return {"type": "table", "data": [], "title": "No Data"}

        # Simple fallback logic
        if chart_type == "table":
            return {
                "type": "table",
                "data": data,
                "title": "Query Results",
                "columns": columns,
            }
        elif chart_type == "bar" and len(columns) >= 2:
            return {
                "type": "bar",
                "data": data,
                "title": f"{columns[0]} vs {columns[1]}",
                "x_axis": columns[0],
                "y_axis": columns[1],
            }
        else:
            return {
                "type": "table",
                "data": data,
                "title": "Query Results",
                "columns": columns,
            }

    async def _generate_insights(
        self,
        results: Dict[str, Any],
        natural_query: str,
        organization_id: int,
        user_id: int,
    ) -> List[Dict[str, Any]]:
        """Generate insights from query results."""
        try:
            if not results.get("data"):
                return []

            prompt = f"""Analyze the following query results and provide insights.

            Query: {natural_query}
            Results: {json.dumps(results['data'][:20], default=str)}  # First 20 rows

            Provide 2-3 key insights and 1-2 actionable recommendations.
            Format as JSON array with objects containing:
            - insight: key finding
            - recommendation: actionable advice

            Return only valid JSON array:"""

            insights_json = await self.ai_service.generate_text(
                prompt=prompt,
                temperature=0.4,
                organization_id=organization_id,
                user_id=user_id,
                feature="insights_generation",
            )

            try:
                insights = json.loads(insights_json.strip())
                return insights if isinstance(insights, list) else []
            except json.JSONDecodeError:
                return []

        except Exception as e:
            logger.error(f"Insights generation failed: {str(e)}")
            return []

    async def get_queries(
        self, organization_id: int, skip: int = 0, limit: int = 100
    ) -> List[AIAnalyticsQuery]:
        """Get analytics queries for organization."""
        result = await self.db.execute(
            select(AIAnalyticsQuery)
            .where(AIAnalyticsQuery.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
            .order_by(AIAnalyticsQuery.created_at.desc())
        )
        return result.scalars().all()

    async def get_query(
        self, query_id: int, organization_id: int
    ) -> Optional[AIAnalyticsQuery]:
        """Get a specific query."""
        result = await self.db.execute(
            select(AIAnalyticsQuery).where(
                AIAnalyticsQuery.id == query_id,
                AIAnalyticsQuery.organization_id == organization_id
            )
        )
        return result.scalar_one_or_none()

    async def get_organization_stats(self, organization_id: int) -> Dict[str, Any]:
        """Get analytics usage stats for organization."""
        from sqlalchemy import func

        result = await self.db.execute(
            select(
                func.count(AIAnalyticsQuery.id).label('total_queries'),
                func.sum(AIAnalyticsQuery.tokens_used).label('total_tokens'),
                func.sum(AIAnalyticsQuery.cost).label('total_cost'),
            ).where(AIAnalyticsQuery.organization_id == organization_id)
        )
        stats = result.first()

        return {
            "total_queries": stats.total_queries or 0,
            "total_tokens": stats.total_tokens or 0,
            "total_cost": float(stats.total_cost or 0),
        }
