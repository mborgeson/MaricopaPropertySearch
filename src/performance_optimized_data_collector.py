"""
Performance-Optimized Data Collector
High-speed property data collection with progressive loading and parallel processing
Target: <3 seconds total collection time
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from src.parallel_api_client import HighPerformanceMaricopaAPIClient
from src.logging_config import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)

@dataclass
class CollectionTask:
    """Represents a data collection task"""
    name: str
    priority: int  # 1=highest, 3=lowest
    estimated_time: float
    required: bool = True

@dataclass 
class ProgressiveResults:
    """Progressive loading results structure"""
    apn: str
    stage: str  # 'basic', 'detailed', 'complete'
    completion_percentage: float
    data: Dict[str, Any]
    collection_time: float
    errors: List[str]

class PerformanceOptimizedDataCollector:
    """
    High-performance data collector with progressive loading:
    Stage 1: Basic property info (<1 second)
    Stage 2: Tax and valuation data (<2 seconds) 
    Stage 3: Sales and document history (<3 seconds total)
    """
    
    def __init__(self, db_manager, config_manager):
        self.db_manager = db_manager
        self.config_manager = config_manager
        
        # Initialize high-performance API client
        self.api_client = HighPerformanceMaricopaAPIClient(config_manager)
        
        # Performance tracking
        self.collection_stats = {
            'total_collections': 0,
            'avg_collection_time': 0.0,
            'cache_hit_rate': 0.0,
            'stage_times': {'basic': [], 'detailed': [], 'complete': []}
        }
        
        logger.info("Performance-Optimized Data Collector initialized")
    
    async def collect_property_data_progressive(self, apn: str, callback=None) -> ProgressiveResults:
        """
        Progressive property data collection with real-time updates
        Returns data as it becomes available for immediate UI updates
        """
        logger.info(f"Starting progressive data collection for APN: {apn}")
        start_time = time.time()
        
        results = ProgressiveResults(
            apn=apn,
            stage='initializing',
            completion_percentage=0.0,
            data={},
            collection_time=0.0,
            errors=[]
        )
        
        try:
            # STAGE 1: Basic property info (Target: <1 second)
            stage_start = time.time()
            basic_data = await self._collect_basic_data_fast(apn)
            stage_time = time.time() - stage_start
            
            results.stage = 'basic'
            results.completion_percentage = 33.3
            results.data.update(basic_data)
            results.collection_time = time.time() - start_time
            self.collection_stats['stage_times']['basic'].append(stage_time)
            
            if callback:
                callback(results)
            
            logger.info(f"Stage 1 (Basic) completed in {stage_time:.3f}s for APN: {apn}")
            
            # STAGE 2: Detailed property data (Target: <2 seconds total)
            stage_start = time.time()
            detailed_data = await self._collect_detailed_data_fast(apn, basic_data)
            stage_time = time.time() - stage_start
            
            results.stage = 'detailed'
            results.completion_percentage = 66.6
            results.data.update(detailed_data)
            results.collection_time = time.time() - start_time
            self.collection_stats['stage_times']['detailed'].append(stage_time)
            
            if callback:
                callback(results)
            
            logger.info(f"Stage 2 (Detailed) completed in {stage_time:.3f}s for APN: {apn}")
            
            # STAGE 3: Extended data (sales, documents) (Target: <3 seconds total)
            stage_start = time.time()
            extended_data = await self._collect_extended_data_fast(apn, results.data)
            stage_time = time.time() - stage_start
            
            results.stage = 'complete'
            results.completion_percentage = 100.0
            results.data.update(extended_data)
            results.collection_time = time.time() - start_time
            self.collection_stats['stage_times']['complete'].append(stage_time)
            
            if callback:
                callback(results)
            
            logger.info(f"Stage 3 (Extended) completed in {stage_time:.3f}s for APN: {apn}")
            
            # Save to database asynchronously (non-blocking)
            asyncio.create_task(self._save_data_async(results.data))
            
            # Update collection stats
            self._update_performance_stats(results.collection_time)
            
            logger.info(f"Progressive collection completed in {results.collection_time:.3f}s for APN: {apn}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in progressive data collection for APN {apn}: {e}")
            results.errors.append(str(e))
            results.collection_time = time.time() - start_time
            return results
    
    async def _collect_basic_data_fast(self, apn: str) -> Dict[str, Any]:
        """Stage 1: Collect basic property information quickly"""
        logger.debug(f"Collecting basic data for APN: {apn}")
        
        # Single fast API call for basic property info
        basic_data = await self.api_client._make_async_request(f'/parcel/{apn}/')
        
        if basic_data:
            return {
                'basic_property_info': basic_data,
                'data_collection_stage': 'basic',
                'basic_data_available': True
            }
        else:
            return {
                'data_collection_stage': 'basic',
                'basic_data_available': False
            }
    
    async def _collect_detailed_data_fast(self, apn: str, basic_data: Dict) -> Dict[str, Any]:
        """Stage 2: Collect detailed property data using parallel requests"""
        logger.debug(f"Collecting detailed data for APN: {apn}")
        
        # Use parallel API client for detailed data
        detailed_data = await self.api_client._get_detailed_property_data_parallel(apn)
        
        result = {
            'detailed_data_available': bool(detailed_data),
            'data_collection_stage': 'detailed'
        }
        
        if detailed_data:
            result.update(detailed_data)
            
            # Process valuations for immediate display
            if 'valuations' in detailed_data and detailed_data['valuations']:
                result['valuation_summary'] = self._process_valuations_fast(detailed_data['valuations'])
            
            # Process residential details
            if 'residential_details' in detailed_data and detailed_data['residential_details']:
                result['property_summary'] = self._process_residential_fast(detailed_data['residential_details'])
        
        return result
    
    async def _collect_extended_data_fast(self, apn: str, existing_data: Dict) -> Dict[str, Any]:
        """Stage 3: Collect extended data (sales history, documents) with timeout"""
        logger.debug(f"Collecting extended data for APN: {apn}")
        
        # Define extended data tasks with timeouts
        tasks = []
        
        # Sales history (if not in detailed data)
        if 'sales_history' not in existing_data:
            tasks.append(asyncio.create_task(
                self._get_sales_history_fast(apn),
                name='sales_history'
            ))
        
        # Property documents
        tasks.append(asyncio.create_task(
            self._get_documents_fast(apn),
            name='documents'
        ))
        
        # Tax information (from scraper if needed)
        if 'tax_records' not in existing_data:
            tasks.append(asyncio.create_task(
                self._get_tax_info_fast(apn),
                name='tax_info'
            ))
        
        # Wait for all tasks with timeout
        extended_data = {
            'data_collection_stage': 'complete',
            'extended_data_available': False
        }
        
        if tasks:
            try:
                # Wait for all tasks with 2-second timeout for this stage
                completed_tasks = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=2.0
                )
                
                for i, result in enumerate(completed_tasks):
                    task_name = tasks[i].get_name()
                    if not isinstance(result, Exception) and result:
                        extended_data[task_name] = result
                        extended_data['extended_data_available'] = True
                        logger.debug(f"Extended data collected: {task_name}")
                    else:
                        logger.debug(f"Extended data failed: {task_name} - {result}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Extended data collection timed out for APN: {apn}")
                # Cancel remaining tasks
                for task in tasks:
                    task.cancel()
        
        return extended_data
    
    async def _get_sales_history_fast(self, apn: str) -> Optional[List[Dict]]:
        """Fast sales history collection with timeout"""
        try:
            sales_data = await asyncio.wait_for(
                self.api_client._make_async_request(f'/parcel/{apn}/sales/'),
                timeout=1.5
            )
            return sales_data if sales_data else []
        except asyncio.TimeoutError:
            logger.warning(f"Sales history timeout for APN: {apn}")
            return []
        except Exception as e:
            logger.error(f"Sales history error for APN {apn}: {e}")
            return []
    
    async def _get_documents_fast(self, apn: str) -> Optional[List[Dict]]:
        """Fast document collection with timeout"""
        try:
            docs_data = await asyncio.wait_for(
                self.api_client._make_async_request(f'/parcel/{apn}/documents/'),
                timeout=1.5
            )
            return docs_data if docs_data else []
        except asyncio.TimeoutError:
            logger.warning(f"Documents timeout for APN: {apn}")
            return []
        except Exception as e:
            logger.error(f"Documents error for APN {apn}: {e}")
            return []
    
    async def _get_tax_info_fast(self, apn: str) -> Optional[List[Dict]]:
        """Fast tax information collection"""
        try:
            tax_data = await asyncio.wait_for(
                self.api_client._make_async_request(f'/parcel/{apn}/tax-info/'),
                timeout=1.0
            )
            return tax_data if tax_data else []
        except asyncio.TimeoutError:
            logger.warning(f"Tax info timeout for APN: {apn}")
            return []
        except Exception as e:
            logger.error(f"Tax info error for APN {apn}: {e}")
            return []
    
    def _process_valuations_fast(self, valuations: List[Dict]) -> Dict[str, Any]:
        """Fast processing of valuation data for immediate display"""
        if not valuations:
            return {}
        
        latest = valuations[0]
        return {
            'latest_tax_year': latest.get('TaxYear'),
            'latest_assessed_value': self._safe_int(latest.get('FullCashValue')),
            'latest_limited_value': self._safe_int(latest.get('LimitedPropertyValue')),
            'property_use': latest.get('PEPropUseDesc'),
            'tax_area': latest.get('TaxAreaCode'),
            'valuation_count': len(valuations)
        }
    
    def _process_residential_fast(self, res_details: Dict) -> Dict[str, Any]:
        """Fast processing of residential details"""
        return {
            'year_built': self._safe_int(res_details.get('ConstructionYear')),
            'lot_size_sqft': self._safe_int(res_details.get('LotSize')),
            'living_area_sqft': self._safe_int(res_details.get('LivableSpace')),
            'pool': res_details.get('Pool', False),
            'bedrooms': self._safe_int(res_details.get('Bedrooms')),
            'bathrooms': self._safe_float(res_details.get('Bathrooms'))
        }
    
    async def _save_data_async(self, property_data: Dict):
        """Asynchronous database save (non-blocking)"""
        try:
            # Run database save in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                self.db_manager.save_comprehensive_property_data,
                property_data
            )
            logger.debug("Property data saved to database")
        except Exception as e:
            logger.error(f"Error saving property data: {e}")
    
    def _update_performance_stats(self, collection_time: float):
        """Update performance statistics"""
        self.collection_stats['total_collections'] += 1
        
        # Update average collection time
        prev_avg = self.collection_stats['avg_collection_time']
        count = self.collection_stats['total_collections']
        self.collection_stats['avg_collection_time'] = (prev_avg * (count - 1) + collection_time) / count
        
        # Update cache hit rate from API client
        api_stats = self.api_client.get_performance_stats()
        self.collection_stats['cache_hit_rate'] = api_stats['cache_hit_rate']
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to int"""
        if not value or value == '':
            return None
        try:
            return int(str(value).replace(',', '').strip())
        except (ValueError, AttributeError):
            return None
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        if not value or value == '':
            return None
        try:
            return float(str(value).replace(',', '').strip())
        except (ValueError, AttributeError):
            return None
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        api_stats = self.api_client.get_performance_stats()
        
        stage_averages = {}
        for stage, times in self.collection_stats['stage_times'].items():
            stage_averages[f'{stage}_avg_time'] = sum(times) / max(len(times), 1) if times else 0.0
        
        return {
            'collection_stats': self.collection_stats,
            'api_performance': api_stats,
            'stage_performance': stage_averages,
            'performance_targets': {
                'basic_target': 1.0,
                'detailed_target': 2.0,
                'complete_target': 3.0
            }
        }
    
    def collect_property_data_sync(self, apn: str, callback=None) -> ProgressiveResults:
        """Synchronous wrapper for progressive data collection"""
        return asyncio.run(self.collect_property_data_progressive(apn, callback))
    
    async def close(self):
        """Clean up resources"""
        await self.api_client.close()
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'api_client'):
            asyncio.run(self.close())