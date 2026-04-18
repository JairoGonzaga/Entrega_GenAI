import { CatalogHeader } from './components/CatalogHeader'
import { CatalogFilters } from './components/CatalogFilters'
import { ProductDetailsPanel } from './components/ProductDetailsPanel'
import { ProductFormModal } from './components/ProductFormModal'
import { ProductListPanel } from './components/ProductListPanel'
import { useCatalogPanel } from './useCatalogPanel'
import { formatCurrency, formatDate } from './utils'

export function CatalogPage() {
  const catalog = useCatalogPanel()

  return (
    <main className="dashboard">
      <CatalogHeader onCreate={catalog.openCreateForm} />

      <CatalogFilters
        search={catalog.search}
        onSearchChange={catalog.setSearch}
        selectedCategories={catalog.selectedCategories}
        allCategories={catalog.allCategories}
        isCategoryOpen={catalog.isCategoryOpen}
        onToggleCategoryOpen={() => catalog.setIsCategoryOpen((current) => !current)}
        onToggleCategory={catalog.toggleCategory}
        minRating={catalog.minRating}
        onMinRatingChange={catalog.setMinRating}
      />

      {catalog.error && <p className="error">{catalog.error}</p>}
      {catalog.categoriesError && <p className="error">{catalog.categoriesError}</p>}

      <section className="content-grid">
        <ProductListPanel
          items={catalog.items}
          total={catalog.total}
          page={catalog.page}
          totalPages={catalog.totalPages}
          isLoading={catalog.isLoading}
          selectedId={catalog.selectedId}
          onSelectItem={catalog.setSelectedId}
          onEditItem={catalog.openEditForm}
          onDeleteItem={(id) => void catalog.handleDeleteProduct(id)}
          onPreviousPage={() => void catalog.goToPage(catalog.page - 1)}
          onNextPage={() => void catalog.goToPage(catalog.page + 1)}
          formatCurrency={formatCurrency}
        />

        <ProductDetailsPanel
          detail={catalog.detail}
          isDetailLoading={catalog.isDetailLoading}
          formatCurrency={formatCurrency}
          formatDate={formatDate}
        />
      </section>

      <ProductFormModal
        isOpen={catalog.isFormOpen}
        editingId={catalog.editingId}
        formData={catalog.formData}
        allCategories={catalog.allCategories}
        showCategorySuggestions={catalog.showCategorySuggestions}
        isSubmitting={catalog.isSubmitting}
        onClose={catalog.closeForm}
        onSubmit={catalog.handleFormSubmit}
        onFieldChange={catalog.updateFormField}
        onCategorySuggestionSelect={catalog.selectCategorySuggestion}
        onCategoryFocus={() => catalog.setShowCategorySuggestions(Boolean(catalog.formData.categoria_produto.trim()))}
        onCategoryBlur={() => window.setTimeout(() => catalog.setShowCategorySuggestions(false), 120)}
      />
    </main>
  )
}

export default CatalogPage