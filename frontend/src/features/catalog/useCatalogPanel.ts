import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  fetchCategories,
  fetchWithFallback,
  fetchProductDetail,
  fetchProductList,
} from './api'
import { emptyForm, PAGE_SIZE, type ProductDetail, type ProductFormData, type ProductListItem } from './types'

export function useCatalogPanel() {
  const [items, setItems] = useState<ProductListItem[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [search, setSearch] = useState('')
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [minRating, setMinRating] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [debouncedCategories, setDebouncedCategories] = useState<string[]>([])
  const [debouncedMinRating, setDebouncedMinRating] = useState('')
  const [page, setPage] = useState(1)
  const [allCategories, setAllCategories] = useState<string[]>([])
  const [categoriesError, setCategoriesError] = useState<string | null>(null)
  const [isCategoryOpen, setIsCategoryOpen] = useState(false)

  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<ProductDetail | null>(null)
  const [isDetailLoading, setIsDetailLoading] = useState(false)

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState<ProductFormData>(emptyForm)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showCategorySuggestions, setShowCategorySuggestions] = useState(false)

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  async function loadProducts(currentPage = page) {
    setIsLoading(true)
    setError(null)

    const params = new URLSearchParams({
      skip: String((currentPage - 1) * PAGE_SIZE),
      limit: String(PAGE_SIZE),
    })

    if (debouncedSearch.trim()) {
      params.set('busca', debouncedSearch.trim())
    }
    if (debouncedCategories.length > 0) {
      debouncedCategories.forEach((category) => {
        if (category.trim()) {
          params.append('categoria', category.trim())
        }
      })
    }
    if (debouncedMinRating.trim()) {
      params.set('nota_min', debouncedMinRating.trim())
    }

    try {
      const data = await fetchProductList(`/produtos?${params.toString()}`)
      setItems(data.itens)
      setTotal(data.total)

      if (allCategories.length === 0) {
        try {
          const categories = await fetchCategories()
          console.info('categorias:total', categories.length)
          setAllCategories(categories)
          setCategoriesError(null)
        } catch (err) {
          setCategoriesError(err instanceof Error ? err.message : 'Erro ao carregar categorias')
          const fallback = Array.from(
            new Set(data.itens.map((item) => item.categoria_produto).filter(Boolean)),
          ).sort()
          if (fallback.length > 0) {
            setAllCategories(fallback)
          }
        }
      }

      if (data.itens.length === 0) {
        setSelectedId(null)
        setDetail(null)
        return
      }

      const hasSelected = selectedId
        ? data.itens.some((item) => item.id_produto === selectedId)
        : false

      if (!hasSelected) {
        setSelectedId(data.itens[0].id_produto)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro inesperado')
    } finally {
      setIsLoading(false)
    }
  }

  async function loadDetail(productId: string) {
    setIsDetailLoading(true)
    setError(null)
    try {
      const data = await fetchProductDetail(productId)
      setDetail(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar detalhes')
      setDetail(null)
    } finally {
      setIsDetailLoading(false)
    }
  }

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedSearch(search)
      setDebouncedCategories(selectedCategories)
      setDebouncedMinRating(minRating)
    }, 300)

    return () => {
      window.clearTimeout(timeout)
    }
  }, [search, selectedCategories, minRating])

  useEffect(() => {
    void loadProducts(1)
    setPage(1)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch, debouncedCategories, debouncedMinRating])

  useEffect(() => {
    if (!selectedId) {
      return
    }

    void loadDetail(selectedId)
  }, [selectedId])

  function openCreateForm() {
    setEditingId(null)
    setFormData(emptyForm)
    setShowCategorySuggestions(false)
    setIsFormOpen(true)
  }

  function openEditForm(item: ProductListItem) {
    setEditingId(item.id_produto)
    setFormData({
      nome_produto: item.nome_produto,
      categoria_produto: item.categoria_produto,
      descricao_produto: item.descricao_produto,
      preco_base: item.preco_base,
      peso_produto_gramas: detail?.medidas.peso_produto_gramas ?? null,
      comprimento_centimetros: detail?.medidas.comprimento_centimetros ?? null,
      altura_centimetros: detail?.medidas.altura_centimetros ?? null,
      largura_centimetros: detail?.medidas.largura_centimetros ?? null,
    })
    setShowCategorySuggestions(false)
    setIsFormOpen(true)
  }

  function selectCategorySuggestion(value: string) {
    setFormData((prev) => ({ ...prev, categoria_produto: value }))
    setShowCategorySuggestions(false)
  }

  function toggleCategory(value: string) {
    setSelectedCategories((prev) =>
      prev.includes(value)
        ? prev.filter((current) => current !== value)
        : [...prev, value],
    )
  }

  function updateFormField(field: keyof ProductFormData, value: ProductFormData[keyof ProductFormData]) {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  async function handleFormSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSubmitting(true)
    setError(null)

    const payload: ProductFormData = {
      nome_produto: formData.nome_produto.trim(),
      categoria_produto: formData.categoria_produto.trim(),
      descricao_produto: formData.descricao_produto?.trim() || null,
      preco_base: formData.preco_base,
      peso_produto_gramas: formData.peso_produto_gramas,
      comprimento_centimetros: formData.comprimento_centimetros,
      altura_centimetros: formData.altura_centimetros,
      largura_centimetros: formData.largura_centimetros,
    }

    try {
      const isEditing = Boolean(editingId)

      const response = await fetchWithFallback(isEditing ? `/produtos/${editingId}` : '/produtos', {
        method: isEditing ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const body = await response.json().catch(() => null)
        const detailMessage = body?.detail ?? 'Nao foi possivel salvar o produto'
        throw new Error(detailMessage)
      }

      setIsFormOpen(false)
      await loadProducts(page)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar produto')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleDeleteProduct(id: string) {
    const confirmed = window.confirm('Deseja remover este produto?')
    if (!confirmed) {
      return
    }

    setError(null)
    try {
      const response = await fetchWithFallback(`/produtos/${id}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        const body = await response.json().catch(() => null)
        throw new Error(body?.detail ?? 'Nao foi possivel remover o produto')
      }

      if (selectedId === id) {
        setSelectedId(null)
      }

      await loadProducts(page)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao remover produto')
    }
  }

  async function goToPage(nextPage: number) {
    const boundedPage = Math.max(1, Math.min(totalPages, nextPage))
    setPage(boundedPage)
    await loadProducts(boundedPage)
  }

  function closeForm() {
    setIsFormOpen(false)
  }

  return {
    items,
    total,
    isLoading,
    error,
    search,
    setSearch,
    selectedCategories,
    minRating,
    setMinRating,
    page,
    totalPages,
    allCategories,
    categoriesError,
    isCategoryOpen,
    setIsCategoryOpen,
    selectedId,
    setSelectedId,
    detail,
    isDetailLoading,
    isFormOpen,
    editingId,
    formData,
    isSubmitting,
    showCategorySuggestions,
    setShowCategorySuggestions,
    openCreateForm,
    openEditForm,
    closeForm,
    toggleCategory,
    selectCategorySuggestion,
    updateFormField,
    handleFormSubmit,
    handleDeleteProduct,
    goToPage,
  }
}